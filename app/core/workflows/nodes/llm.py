from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from config.prompts import APPOINTMENT_PROMPT, CONTACT_PROMPT, HANDOFF_PROMPT
from config.settings import settings


class LLMNode:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.google_api_key,
            temperature=0.3
        )
        self.generic = ChatPromptTemplate.from_template("{prompt}")

    async def __call__(self, state):
        # Skip LLM if intent is appointment or FAQ
        if state.get("intent") == "appointment":
            return state
        if state.get("intent") == "faqs":
            return state

        # Safety: Override if an old intent like "intake" is still around
        if state.get("intent") == "intake":
            state["intent"] = "appointment"

        # Define available prompt mappings
        prompt_map = {
            "handoff": HANDOFF_PROMPT,
        }

        # Use the mapped prompt or fallback
        prompt = prompt_map.get(state.get("intent"))

        if not prompt:
            state["final_response"] = (
                "🤖 Sorry, I'm not sure how to handle that request right now."
            )
            return state

        chain = self.generic | self.llm
        out = await chain.ainvoke({"prompt": prompt})

        # Handle response structure from LLM
        state["final_response"] = out[0] if isinstance(out, list) else out
        return state
