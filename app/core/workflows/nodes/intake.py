from config.prompts import INTAKE_PROMPT

class IntakeFormNode:
    async def __call__(self, state):
        state["final_response"] = INTAKE_PROMPT.strip()
        return state
