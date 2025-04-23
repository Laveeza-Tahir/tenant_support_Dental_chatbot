from config.prompts import CONTACT_PROMPT

class StaticInfoNode:
    async def __call__(self, state):
        state["final_response"] = CONTACT_PROMPT.strip()
        return state
