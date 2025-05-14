from langchain_core.messages import AIMessage
from typing import Dict, Any

async def output_processor(self, state: Dict[str, Any]) -> Dict[str, Any]:
    """Process the output and prepare final response"""
    # Add the AI response to messages
    state["messages"].append(AIMessage(content=state["response"]))
        
        # Extract source information
    sources = []
    if "sources" in state and state["sources"]:
        sources = [s for s in state["sources"] if s != "unknown"]
        
    state["final_response"] = {
        "response": state["response"],
        "sources": sources,
        "session_data": state.get("session_data", {})
    }
        
    return state
