from typing import List, Dict, Any
from langchain_core.documents import Document
from app.core.chroma_manager import query_collection

class ChromaRetriever:
    """A retriever that uses ChromaDB collections for each user"""
    
    def __init__(self, k: int = 5):
        """Initialize the retriever with k results to return"""
        self.k = k
        
    def retrieve(self, query: str, user_id: str) -> List[Document]:
        """Retrieve documents from ChromaDB based on the query"""
        try:
            print(f"Attempting ChromaDB retrieval for user_id: {user_id} with query: {query[:50]}...")
            
            # Query the user's ChromaDB collection
            results = query_collection(user_id, query)
            documents = []
            
            # Debug info
            print(f"ChromaDB raw results structure: {type(results)}")
            if isinstance(results, dict):
                for key in results:
                    if isinstance(results[key], list):
                        print(f"ChromaDB '{key}' has {len(results[key])} items")
                        if results[key] and isinstance(results[key][0], list):
                            print(f"- First item contains {len(results[key][0])} elements (nested structure)")
            
            # Process documents from results
            if results and isinstance(results, dict) and 'documents' in results and results['documents']:
                doc_texts = []
                if isinstance(results['documents'], list):
                    if results['documents'] and isinstance(results['documents'][0], list):
                        doc_texts = results['documents'][0]  # Nested list case
                        print(f"Processing nested documents structure with {len(doc_texts)} items")
                    else:
                        doc_texts = results['documents']  # Flat list case
                        print(f"Processing flat documents structure with {len(doc_texts)} items")
                
                # Process metadata
                metadatas = []
                if 'metadatas' in results and results['metadatas']:
                    if isinstance(results['metadatas'], list):
                        if results['metadatas'] and isinstance(results['metadatas'][0], list):
                            metadatas = results['metadatas'][0]  # Nested list case
                        else:
                            metadatas = results['metadatas']  # Flat list case
                
                # Get distances/scores if available for better ranking
                distances = []
                if 'distances' in results and results['distances']:
                    if isinstance(results['distances'], list):
                        if results['distances'] and isinstance(results['distances'][0], list):
                            distances = results['distances'][0]  # Nested list case
                        else:
                            distances = results['distances']  # Flat list case
                
                # Create Document objects
                for i, text in enumerate(doc_texts):
                    if not text or not isinstance(text, str):
                        print(f"Skipping invalid document at index {i}: {text}")
                        continue
                        
                    metadata = metadatas[i] if i < len(metadatas) else {"user_id": user_id}
                    distance = distances[i] if i < len(distances) else None
                    
                    # Create a document with enhanced metadata
                    documents.append(Document(
                        page_content=text,
                        metadata={
                            "source": f"User {user_id}'s FAQ", 
                            "user_id": metadata.get("user_id", user_id),
                            "distance": distance,
                            "retriever": "chroma"  # Mark the source retriever
                        }
                    ))
            
            print(f"Successfully created {len(documents)} Document objects from ChromaDB")
            return documents[:self.k]  # Limit to k results
        
        except Exception as e:
            print(f"Error retrieving from ChromaDB: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []  # Return empty list on error
