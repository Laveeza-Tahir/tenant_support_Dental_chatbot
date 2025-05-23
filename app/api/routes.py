from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.workflows.main_workflow import DentalWorkflow
from app.models.session import sessions, get_session_messages
from app.core.classifier import detect_intent
from collections import Counter
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import LatentDirichletAllocation
import numpy as np
from app.core.chroma_manager import query_collection, list_all_collections
from app.api.auth import get_current_user, User

router = APIRouter()

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    sources: list[str]

class HotTopicsResponse(BaseModel):
    topics: list[dict]
    total_queries: int

class DbCollectionsResponse(BaseModel):
    collections: list[str]

@router.get("/collections", response_model=DbCollectionsResponse)
async def list_collections():
    """List all available collections in the database."""
    collections = list_all_collections()
    return DbCollectionsResponse(collections=collections)

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, current_user: User = Depends(get_current_user)):
    # Use complete DentalWorkflow for intent-based routing
    workflow = DentalWorkflow()
    
    # Add user_id to session for ChromaDB access
    user_id = str(current_user.id)
    
    try:
        # Load existing session state
        state = await workflow._load_session(req.session_id)
        # Add user_id to state
        state["user_id"] = user_id
        # Save state with user_id
        await workflow._save_session(req.session_id, state)

        # Run the full workflow with proper session management
        response_text = await workflow.run(req.session_id, req.message)
        
        # Get session state to extract sources
        session = await workflow._load_session(req.session_id)
        # Extract just the source names from the retrieved_sources dictionaries
        retrieved_sources = session.get("retrieved_sources", [])
        sources = [source["source"] for source in retrieved_sources] if retrieved_sources else ["unknown"]
        
        # Ensure response_text is a string
        if isinstance(response_text, dict) and "response" in response_text:
            response_text = response_text["response"]
    except Exception as e:
        print(f"Error in workflow: {str(e)}")
        # Fallback to direct ChromaDB query if workflow fails
        results = query_collection(user_id, req.message)

        # Combine results into a response - handle nested lists properly
        if 'documents' in results and len(results['documents']) > 0:
            if isinstance(results['documents'][0], list):  # If documents is a list of lists
                documents = results['documents'][0]
            else:  # If documents is just a list of strings
                documents = results['documents']
            response_text = "\n".join(documents)
        else:
            response_text = "No relevant information found."

        # Extract user_id from metadata as sources
        if 'metadatas' in results and len(results['metadatas']) > 0:
            if isinstance(results['metadatas'][0], list):  # If metadatas is a list of lists
                metadatas = results['metadatas'][0]
            else:  # If metadatas is just a list of dicts
                metadatas = results['metadatas']
            # Create source strings from metadatas
            sources = [f"User {metadata.get('user_id', 'unknown')}'s FAQ" for metadata in metadatas]
        else:
            sources = ["unknown"]

    return ChatResponse(response=response_text, sources=sources)

@router.get("/debug-collections")
async def debug_collections():
    """Debug endpoint to list all collections and try to create a test collection."""
    try:
        from app.core.chroma_manager import chroma_client, create_or_update_collection
        
        # List existing collections
        collections = list_all_collections()
        
        # Try to create a test collection
        test_text = "Q: What is a test?\nA: This is a test collection."
        create_or_update_collection("test_user", test_text)
        
        # List collections after creation
        new_collections = list_all_collections()
        
        return {
            "before": collections,
            "after": new_collections,
            "chroma_client_type": str(type(chroma_client)),
            "persist_directory": getattr(chroma_client, "_path", "No path attribute found")
        }
    except Exception as e:
        return {"error": str(e), "type": str(type(e))}

async def extract_topics_nlp(messages, num_topics=5):
    """Extract topics using NLP (LDA) from a list of messages"""
    if not messages or len(messages) < 3:
        # Fall back to basic intent classification for small datasets
        topics_counter = Counter()
        for message in messages:
            intent = detect_intent(message)
            topics_counter[intent] += 1
        return [{"topic": topic, "count": count} for topic, count in topics_counter.most_common()]
    
    # Vectorize the messages
    vectorizer = TfidfVectorizer(
        max_features=100,
        stop_words='english',
        min_df=2,
        max_df=0.8
    )
    
    try:
        X = vectorizer.fit_transform(messages)
        feature_names = vectorizer.get_feature_names_out()
        
        # Use LDA for topic modeling
        lda = LatentDirichletAllocation(
            n_components=min(num_topics, len(messages) // 2),
            random_state=42
        )
        lda.fit(X)
        
        # Extract top words for each topic
        topics = []
        word_importance = np.argsort(lda.components_, axis=1)[:, ::-1]
        
        for topic_idx, topic in enumerate(lda.components_):
            # Get the top 5 words for this topic
            top_words = [feature_names[i] for i in word_importance[topic_idx, :5]]
            topic_name = ", ".join(top_words)
            
            # Count how many documents are primarily about this topic
            doc_topic_dist = lda.transform(X)
            count = np.sum(np.argmax(doc_topic_dist, axis=1) == topic_idx)
            
            topics.append({
                "topic": topic_name,
                "count": int(count),
                "keywords": top_words
            })
        
        # Sort by count (descending)
        return sorted(topics, key=lambda x: x["count"], reverse=True)
    
    except (ValueError, IndexError):
        # Fall back to basic intent classification if vectorization fails
        topics_counter = Counter()
        for message in messages:
            intent = detect_intent(message)
            topics_counter[intent] += 1
        return [{"topic": topic, "count": count} for topic, count in topics_counter.most_common()]

@router.get("/hot-topics", response_model=HotTopicsResponse)
async def get_hot_topics():
    # Get all sessions from database
    all_sessions = await sessions.find().to_list(length=1000)
    
    # Extract user messages from all sessions
    user_messages = []
    for session in all_sessions:
        messages = session.get("messages", [])
        for message in messages:
            if message.get("sender") == "user":
                user_messages.append(message.get("text", ""))
    
    # Use NLP to extract topics
    topics = await extract_topics_nlp(user_messages)
    
    return HotTopicsResponse(
        topics=topics,
        total_queries=len(user_messages)
    )

@router.get("/session/{session_id}/topics", response_model=HotTopicsResponse)
async def get_session_topics(session_id: str):
    # Get messages for the specific session
    messages = await get_session_messages(session_id)
    
    # Extract user messages only
    user_messages = [msg.get("text", "") for msg in messages if msg.get("sender") == "user"]
    
    # Use NLP to extract topics
    topics = await extract_topics_nlp(user_messages)
    
    return HotTopicsResponse(
        topics=topics,
        total_queries=len(user_messages)
    )

@router.get("/debug-chroma")
async def debug_chroma():
    """Debug endpoint to check ChromaDB state."""
    try:
        from app.core.chroma_manager import chroma_client, create_or_update_collection, list_all_collections
        import os
        
        # Get information about the ChromaDB client
        client_info = {
            "type": str(type(chroma_client)),
            "persist_directory": getattr(chroma_client, "_path", "In-memory (no path)")
        }
        
        # List existing collections
        collections = list_all_collections()
        
        # Try to create a test collection
        test_text = "Q: What is a test?\nA: This is a test collection."
        try:
            create_or_update_collection("test_debug", test_text)
            test_creation = "Success"
        except Exception as e:
            test_creation = f"Failed: {str(e)}"
        
        # List collections after creation attempt
        new_collections = list_all_collections()
        
        return {
            "client_info": client_info,
            "collections_before": collections,
            "test_creation": test_creation,
            "collections_after": new_collections,
        }
    except Exception as e:
        return {"error": str(e), "type": str(type(e))}