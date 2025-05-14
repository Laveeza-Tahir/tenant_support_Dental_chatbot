from typing import Dict, Any

async def input_processor(self, state: Dict[str, Any]) -> Dict[str, Any]:
    """Process user input"""
    # Extract the latest user message
    latest_message = state["messages"][-1].content
    state["user_query"] = latest_message
    return state