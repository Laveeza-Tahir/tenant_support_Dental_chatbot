from langgraph.graph import state
from app.models.session import save_session_message
from langchain_core.messages import AIMessage

class OutputNode:
    async def __call__(self, state: state) -> dict:
        final_resp = state["final_response"]

        # If it's an AIMessage, extract the content cleanly
        if isinstance(final_resp, AIMessage):
            resp_text = final_resp.content
        else:
            resp_text = str(final_resp)

        await save_session_message(
            session_id=state["session_id"],
            text=resp_text,
            sender="bot"
        )

        return {
            "response": resp_text,  # Clean, readable response only
            "sources": state.get("retrieved_sources", [])
        }
