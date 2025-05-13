from langgraph.graph import state
from app.core.classifier import detect_intent
import re
import logging

class IntentClassifierNode:
    async def __call__(self, state: state) -> state:
        # Only classify if user_message exists
        if "user_message" in state and state["user_message"]:
            # Check for location-related keywords
            message = state["user_message"].lower()
            
            # Log the message for debugging
            logging.info(f"Classifying message: '{message}'")
            
            # Enhanced patterns for location detection
            location_patterns = [
                r'\b(where|location|address|office|clinic|directions)\b',
                r'\bfind you\b',
                r'\bhow to (get|reach|find)\b',
                r'\bwhere (are|is) (you|your|the)\b',
                r'\blocation of\b',  # Specifically catch "location of clinic"
                r'\boffice location\b',
                r'\bclinic (location|address)\b'
            ]
            
            # Check if any location pattern matches
            is_location_query = any(re.search(pattern, message) for pattern in location_patterns)
            
            # Explicitly check for "location of clinic" type phrases
            if "location" in message and ("clinic" in message or "office" in message or "dental" in message):
                is_location_query = True
                
            if is_location_query:
                logging.info(f"Detected location query: '{message}'")
                state["intent"] = "contact_info"
                # Force override any other intent
                state.pop("pending_intent", None)
            else:
                # Use the default classifier for other queries
                state["intent"] = detect_intent(state["user_message"])
        else:
            # Default intent when no message is present (e.g., after appointment booking)
            state["intent"] = state.get("intent", "greeting")
            
        # Log the classified intent for debugging
        logging.info(f"Classified intent: {state.get('intent')}")
        return state


