from langgraph.graph import state
from app.core.classifier import detect_intent

class IntentClassifierNode:
    async def __call__(self, state: state) -> state:
        state["intent"] = detect_intent(state["user_message"])
        return state
