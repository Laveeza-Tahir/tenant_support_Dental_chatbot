from config.prompts import HANDOFF_PROMPT

class LiveChatNode:
    async def __call__(self, state):
        state["final_response"] = HANDOFF_PROMPT.strip()                    
        return state
