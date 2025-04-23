from app.core.workflows.nodes.input import InputNode
from app.core.workflows.nodes.classify import IntentClassifierNode
from app.core.workflows.nodes.faq import FAQNode
from app.core.workflows.nodes.appointment import AppointmentNode
from app.core.workflows.nodes.intake import IntakeFormNode
from app.core.workflows.nodes.static_info import StaticInfoNode
from app.core.workflows.nodes.handoff import LiveChatNode
from app.core.workflows.nodes.llm import LLMNode
from app.core.workflows.nodes.output import OutputNode

class DentalWorkflow:
    def __init__(self):
        self.input = InputNode()
        self.classifier = IntentClassifierNode()
        self.faq = FAQNode()
        self.appointment = AppointmentNode()
        self.intake = IntakeFormNode()
        self.static = StaticInfoNode()
        self.handoff = LiveChatNode()
        self.llm = LLMNode()
        self.output = OutputNode()

    async def run(self, session_id: str, user_message: str):
        state = {"session_id": session_id, "user_message": user_message}
        state = await self.input(state)
        state = await self.classifier(state)

        intent = state["intent"]
        handled = False

        if intent == "appointment":
            state = await self.appointment(state)
            handled = True
        elif intent == "faqs":
            state = await self.faq(state)
            handled = True
        elif intent == "intake":
            state = await self.intake(state)
            handled = True
        elif intent == "contact_info":
            state = await self.static(state)
            handled = True
        elif intent == "handoff":
            state = await self.handoff(state)
            handled = True

        # Call LLM only if none of the above handled it
        if not handled:
            state = await self.llm(state)

        return await self.output(state)
