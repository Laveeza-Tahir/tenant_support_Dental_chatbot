import requests
import google.generativeai as genai

# Initialize Gemini
genai.configure(api_key="AIzaSyApnwVM0hQG6hsMAakzrgI5XPm-tZ-DEr8")
model = genai.GenerativeModel('gemini-2.0-flash')

# Set your chatbot API endpoint
chatbot_url = "http://192.168.1.6:8000/api/chat"

# Start a conversation loop
session_id = "3"
user_message = "hi"

# Send message to chatbot
response =requests.post (
    chatbot_url,
    headers={
        "accept": "application/json",
        "Content-Type": "application/json"
    },
    json={
        "session_id": session_id,
        "message": user_message
    }
)

# Print chatbot reply
if response.ok:
    chatbot_reply = response.json().get("response", "")
    print(f"Chatbot: {chatbot_reply}")

    # Now send chatbot's response to Gemini for next question
    gemini_reply = model.generate_content(f"You are a user talking to a dental chatbot. The chatbot just said: '{chatbot_reply}'. What will you reply?")
    print(f"Gemini (user): {gemini_reply.text}")
else:
    print(f"Error: {response.status_code} - {response.text}")
