from typing import Dict
from app.core.workflows.nodes.input import InputNode
from app.core.workflows.nodes.classify import IntentClassifierNode
from app.core.workflows.nodes.faq import FAQNode
from app.core.workflows.nodes.appointment import AppointmentNode
from app.core.workflows.nodes.static_info import StaticInfoNode
from app.core.workflows.nodes.handoff import LiveChatNode
from app.core.workflows.nodes.llm import LLMNode
from app.core.workflows.nodes.output import OutputNode
from app.models.session import sessions, save_session_message, get_session_messages
from datetime import datetime

class DentalWorkflow:
    def __init__(self):
        self.input = InputNode()
        self.classifier = IntentClassifierNode()
        self.faq = FAQNode()
        self.appointment = AppointmentNode()
        self.static = StaticInfoNode()
        self.handoff = LiveChatNode()
        self.llm = LLMNode()
        self.output = OutputNode()

    async def _load_session(self, session_id: str) -> Dict:
        """Load session state from MongoDB"""
        doc = await sessions.find_one({"session_id": session_id})
        if doc:
            # If user_id isn't already in state, try to extract it from session data
            if "user_id" not in doc and "session_id" in doc:
                # Extract user_id if session_id follows format user_<id>_xyz
                parts = doc["session_id"].split("_")
                if len(parts) > 1 and parts[0] == "user":
                    doc["user_id"] = parts[1]
            return doc
        
        # Create new session
        new_session = {
            "session_id": session_id,
            "state": {},
            "messages": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Extract user_id if session_id follows format user_<id>_xyz
        parts = session_id.split("_")
        if len(parts) > 1 and parts[0] == "user":
            new_session["user_id"] = parts[1]
            
        return new_session

    async def _save_session(self, session_id: str, state: Dict):
        """Save session state to MongoDB"""
        state["updated_at"] = datetime.utcnow()
        await sessions.update_one(
            {"session_id": session_id},
            {"$set": state},
            upsert=True
        )

    async def run(self, session_id: str, user_message: str):
        # Load session state from MongoDB
        state = await self._load_session(session_id)
        
        # Save user message to conversation history
        await save_session_message(session_id, user_message, "user")

        # Update with current user message
        state["user_message"] = user_message
        state["session_id"] = session_id
        
        # Load session state to get user_id
        if "user_id" not in state:
            stored_state = await self._load_session(session_id)
            if "user_id" in stored_state:
                state["user_id"] = stored_state["user_id"]
                print(f"Loaded user_id: {state['user_id']} from session state")

        # Process input and classification
        state = await self.input(state)
        state = await self.classifier(state)

        # Honor any ongoing multi-turn flows
        if state.get("pending_intent"):
            intent = state["pending_intent"]
        else:
            intent = state.get("intent")

        handled = False

        # Appointment flow
        if intent == "appointment":
            # Set pending to persist across turns
            state["pending_intent"] = "appointment"
            state = await self.appointment(state)
            # Clear on completion
            if state.get("intent") == "appointment_completed":
                state.pop("pending_intent", None)
            handled = True

        # FAQs flow
        elif intent == "faqs":
            # User ID should already be extracted higher up in the workflow
            state = await self.faq(state)
            handled = True

        # Static info flow
        elif intent == "contact_info":
            state = await self.static(state)
            handled = True

        # Handoff to live agent
        elif intent == "handoff":
            state = await self.handoff(state)
            handled = True

        # Default: LLM fallback
        if not handled:
            state = await self.llm(state)

        # Save session state to MongoDB
        await self._save_session(session_id, state)

        # Get bot response from output node
        output_result = await self.output(state)
        
        # Extract string response if output_result is a dict
        if isinstance(output_result, dict):
            response_text = output_result.get("response", "")
        else:
            response_text = str(output_result)
        
        # We no longer need to save the bot response to conversation history here
        # as the OutputNode already does that
        
        return response_text
