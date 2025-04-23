from langgraph.graph import state
from app.models.session import save_session_message

class InputNode:
    async def __call__(self, state: state) -> state:
        await save_session_message(
            session_id=state["session_id"],
            text=state["user_message"],
            sender="user"
        )
        return state
