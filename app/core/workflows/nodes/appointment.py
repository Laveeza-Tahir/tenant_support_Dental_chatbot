import os
import requests
from config.prompts import APPOINTMENT_PROMPT
# Load API key from environment variable
CALENDLY_API_KEY = "eyJraWQiOiIxY2UxZTEzNjE3ZGNmNzY2YjNjZWJjY2Y4ZGM1YmFmYThhNjVlNjg0MDIzZjdjMzJiZTgzNDliMjM4MDEzNWI0IiwidHlwIjoiUEFUIiwiYWxnIjoiRVMyNTYifQ.eyJpc3MiOiJodHRwczovL2F1dGguY2FsZW5kbHkuY29tIiwiaWF0IjoxNzQ1MzA1MTAyLCJqdGkiOiI4YzdjOTEwZC01NzcxLTQ3NGYtYWEwZi04Mjk0NmIyZjFjYjUiLCJ1c2VyX3V1aWQiOiI0YjZmNTdiYy01MTdlLTQzZTEtYjYwZi1jODNlZmUxNGJjYTIifQ.MuZAvmKVEZ-x3w8WjwAYC3X2-Z0kgXB3SONPOTgI07vjdI_3tp_ho2Cu3pk0HkOnsfmMLmaTaLVvyHTqCL1epQ"

HEADERS = {
    "Authorization": f"Bearer {CALENDLY_API_KEY}",
    "Content-Type": "application/json",
}

def get_calendly_user_uri():
    """
    Fetch the current user's URI (needed to query event types).
    """
    resp = requests.get("https://api.calendly.com/users/me", headers=HEADERS)
    if resp.status_code != 200:
        print(f"[Calendly] /users/me failed: {resp.status_code} {resp.text}")
        return None
    return resp.json().get("resource", {}).get("uri")


def get_calendly_link():
    """
    Fetch the first event type's scheduling link using the authenticated user's URI.
    """
    user_uri = get_calendly_user_uri()
    if not user_uri:
        return None

    url = f"https://api.calendly.com/event_types?user={user_uri}"
    resp = requests.get(url, headers=HEADERS)
    print(f"[DEBUG] GET {url} → {resp.status_code}")

    if resp.status_code != 200:
        print(f"[ERROR] Calendly API response: {resp.text}")
        return None

    items = resp.json().get("collection", [])
    if not items:
        print("[DEBUG] No event types found in Calendly response.")
        return None

    return items[0].get("scheduling_url")


class AppointmentNode:
    """
    Responds to booking intent by returning a Calendly scheduling link.
    """

    async def __call__(self, state):
        user_msg = state.get("user_message", "").lower()

        if any(keyword in user_msg for keyword in ["book", "appointment", "schedule", "visit", "dentist", "checkup"]):
            calendly_link = get_calendly_link()
            if calendly_link:
                state["final_response"] = (
                    " You're all set to book an appointment!"
                    f" ({calendly_link})"
                    " After booking, you'll automatically receive a confirmation email from Calendly."
                )
            else:
                state["final_response"] = (
                    "❌ Sorry, I couldn't fetch your scheduling link right now. "
                    "Please try again later."
                )
        else:
            state["final_response"] = APPOINTMENT_PROMPT.strip()
            
        return state