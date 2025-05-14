from typing import Dict, Any
import logging

async def retrieval(self, state: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve relevant documents"""
    query = state["user_query"]
        
    try:
        # Search the vector database
        docs = await self.vector_db.search(
            query=query,
            collection_name="default",
            k=5
        )
            
        # Store the retrieved documents
        state["docs"] = docs
        state["sources"] = [
            doc.metadata.get("source", "unknown")
            for doc in docs
        ]
            
        # Format document context for the LLM
        context = "\n\n".join([
            f"Document {i+1}:\n{doc.page_content}"
            for i, doc in enumerate(docs)
        ])
            
        state["context"] = context
            
    except Exception as e:
        logging.error(f"Error in retrieval: {e}")
        state["context"] = "No relevant information found."
        state["docs"] = []
        state["sources"] = []
            
    return state
    