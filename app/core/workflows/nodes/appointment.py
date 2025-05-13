# from app.core.workflows.utils.calendar_helper import create_calendar_event

# class AppointmentNode:
#     async def __call__(self, state):
#         user_message = state.get("user_message", "").lower()

#         patient_name = state.get("patient_name")
#         appointment_date = state.get("appointment_date")
#         appointment_time = state.get("appointment_time")

#         # Check which information is missing
#         if not patient_name:
#             state["final_response"] = "👤 What's your full name?"
#             state["awaiting"] = "patient_name"
#             return state

#         if not appointment_date:
#             state["final_response"] = "📅 What date would you like to book? (e.g., 2025-05-05)"
#             state["awaiting"] = "appointment_date"
#             return state

#         if not appointment_time:
#             state["final_response"] = "⏰ What time would you prefer? (e.g., 3 PM)"
#             state["awaiting"] = "appointment_time"
#             return state

#         # All information collected → Book the appointment
#         try:
#             event_link = create_calendar_event(patient_name, appointment_date, appointment_time)
#             state["final_response"] = f"✅ Your appointment is booked successfully!\n\n🔗 Here is your appointment link: {event_link}"
#             state["intent"] = "appointment_completed"

#             # Clear temporary memory
#             state.pop("patient_name", None)
#             state.pop("appointment_date", None)
#             state.pop("appointment_time", None)
#             state.pop("awaiting", None)

#         except Exception as e:
#             state["final_response"] = f"❌ Failed to book appointment: {str(e)}"

#         return state
# Path: app/core/workflows/nodes/appointment.py

import re
import logging
import datetime as dt
from app.core.workflows.utils.calendar_helper import create_calendar_event

class AppointmentNode:
    async def __call__(self, state):
        user_message = state.get("user_message", "").lower().strip()
        
        # For debugging
        logging.info(f"AppointmentNode called with state: {state}")
        
        # Directly detect if this is a new appointment request after a previous one
        if user_message in ["book appointment", "schedule appointment", "new appointment"] and not state.get("awaiting"):
            # Clear any existing appointment data to start fresh
            for key in ["patient_name", "appointment_date", "appointment_time"]:
                state.pop(key, None)
            state["final_response"] = "👤 What's your full name?"
            state["awaiting"] = "patient_name"
            return state

        patient_name = state.get("patient_name")
        appointment_date = state.get("appointment_date")
        appointment_time = state.get("appointment_time")

        # Check if user message contains a common time format
        # This helps when the user repeats the time because the system didn't understand
        time_patterns = [
            r'\b\d{1,2}\s*(?:am|pm|a\.m\.|p\.m\.)\b',   # 3pm, 11am
            r'\b\d{1,2}:\d{2}\s*(?:am|pm|a\.m\.|p\.m\.)\b',  # 3:30pm
            r'\b(?:morning|afternoon|evening|noon)\b'    # natural time expressions
        ]
        
        is_time_input = any(re.search(pattern, user_message, re.IGNORECASE) for pattern in time_patterns)
        
        # Handle the case where user repeats time input
        if is_time_input and state.get("awaiting") != "appointment_time":
            # User is trying to provide time even though we didn't ask for it
            appointment_time = user_message
            state["appointment_time"] = user_message
            logging.info(f"Detected time input outside of time question flow: {appointment_time}")

        # Handle natural language responses for dates and times
        if user_message in ["today", "now", "asap"]:
            # Use today's date if user says "today" or "now"
            today = dt.datetime.now().strftime("%Y-%m-%d")
            if state.get("awaiting") == "appointment_date":
                appointment_date = today
                state["appointment_date"] = today
                state["awaiting"] = None
                state["final_response"] = "⏰ What time would you prefer? (e.g., 3 PM, afternoon, evening)"
                return state

        # Special case for "tomorrow"
        if user_message == "tomorrow" and state.get("awaiting") == "appointment_date":
            tomorrow = (dt.datetime.now() + dt.timedelta(days=1)).strftime("%Y-%m-%d")
            appointment_date = tomorrow
            state["appointment_date"] = tomorrow
            state["awaiting"] = None
            state["final_response"] = "⏰ What time would you prefer? (e.g., 3 PM, afternoon, evening)"
            return state

        # Check which information is missing
        if not patient_name:
            state["final_response"] = "👤 What's your full name?"
            state["awaiting"] = "patient_name"
            return state

        if not appointment_date:
            state["final_response"] = "📅 What date would you like to book? (e.g., today, tomorrow, 2025-05-05)"
            state["awaiting"] = "appointment_date"
            return state

        if not appointment_time:
            state["final_response"] = "⏰ What time would you prefer? (e.g., morning, afternoon, 3 PM)"
            state["awaiting"] = "appointment_time"
            return state

        # All information collected - process appointment
        try:
            # Additional validation before booking
            if not appointment_date or appointment_date.strip() == '':
                # Default to today if date is empty
                appointment_date = dt.datetime.now().strftime("%Y-%m-%d")
                state["appointment_date"] = appointment_date
                logging.warning(f"Empty appointment date, defaulting to today: {appointment_date}")
            
            if not appointment_time or appointment_time.strip() == '':
                # Default to afternoon if time is empty
                appointment_time = "2 PM"
                state["appointment_time"] = appointment_time
                logging.warning(f"Empty appointment time, defaulting to: {appointment_time}")
                
            # Log the appointment details for debugging
            logging.info(f"Booking appointment for {patient_name} on {appointment_date} at {appointment_time}")
            
            # Create a calendar event using the collected information
            event_link = create_calendar_event(patient_name, appointment_date, appointment_time)

            # Build a friendly confirmation message
            confirmation = f"✅ Perfect! Your appointment is booked successfully!\n\n"
            confirmation += f"📋 Details:\n"
            confirmation += f"👤 Name: {patient_name}\n"
            confirmation += f"📅 Date: {appointment_date}\n"
            confirmation += f"⏰ Time: {appointment_time}\n\n"
            confirmation += f"🔗 Here is your appointment link: {event_link}\n\n"
            confirmation += f"You'll receive a reminder before your appointment. Is there anything else I can help you with?"

            # Success: Appointment booked
            state["final_response"] = confirmation

            # Mark the appointment as completed and clear ALL appointment state
            state["intent"] = "appointment_completed"
            state["appointment_status"] = "booked"
            state.pop("pending_intent", None)  # Explicitly clear pending intent
            
            # Clear ALL temporary memory related to the appointment process
            for key in list(state.keys()):
                if key.startswith("appointment_") or key in ["patient_name", "awaiting"]:
                    state.pop(key, None)

            # Set a flag indicating the appointment was just booked
            state["just_booked"] = True

        except Exception as e:
            # Handle any error during the booking process
            error_msg = str(e)
            logging.error(f"Failed to book appointment: {error_msg}")
            state["final_response"] = f"❌ Sorry, I couldn't book your appointment: {error_msg}. Would you like to try again with a different time?"
        
        return state
