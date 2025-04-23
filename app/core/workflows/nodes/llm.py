from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from config.prompts import APPOINTMENT_PROMPT, INTAKE_PROMPT, CONTACT_PROMPT, HANDOFF_PROMPT
from config.settings import settings

class LLMNode:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.google_api_key,
            temperature=0.3
        )
        self.generic = ChatPromptTemplate.from_template(
            "{prompt}"
        )

    async def __call__(self, state):
        if state["intent"] == "faqs":
            return state

        prompt_map = {
            "appointment": APPOINTMENT_PROMPT,
            "intake": INTAKE_PROMPT,
            "contact_info": CONTACT_PROMPT,
            "handoff": HANDOFF_PROMPT
        }
        template = prompt_map.get(state["intent"], state["user_message"])
        chain = self.generic | self.llm
        out = await chain.ainvoke({"prompt": template})
        state["final_response"] = out[0] if isinstance(out, list) else out
        return state
