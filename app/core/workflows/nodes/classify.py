from langgraph.graph import state
from app.core.classifier import detect_intent
from app.core.chroma_manager import list_all_collections, query_collection

class IntentClassifierNode:
    async def __call__(self, state: state) -> state:
        # Basic intent classification
        intent = detect_intent(state["user_message"])
        
        # Check if user has uploaded documents and the query might be related to them
        user_id = state.get("user_id")
        if user_id:
            # Check if a collection exists for this user
            user_collection = f"user_{user_id}"
            all_collections = list_all_collections()
            
            # If user has a collection, favor FAQ intent for general questions
            if user_collection in all_collections:
                # Perform a quick similarity check to see if the query resembles any content
                try:
                    user_query = state["user_message"]
                    results = query_collection(user_id, user_query)
                    
                    # If query returns good results, prefer FAQ intent
                    try:
                        if ('documents' in results and len(results['documents']) > 0 and 
                            'distances' in results and len(results['distances']) > 0 and 
                            isinstance(results['distances'][0], list) and len(results['distances'][0]) > 0 and
                            results['distances'][0][0] < 0.5):
                            # If confidence is high in results, override to FAQ intent
                            intent = "faqs"
                            # Add flag that this is coming from user-uploaded docs
                            state["from_user_docs"] = True
                    except (KeyError, IndexError, TypeError):
                        # If there's any issue with the result format, just continue with the default intent
                        pass
                except Exception:
                    # If query fails, continue with detected intent
                    pass
        
        state["intent"] = intent
        return state
