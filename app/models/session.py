from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
from datetime import datetime
from langchain_core.messages import AIMessage

client = AsyncIOMotorClient(settings.mongo_uri)
db = client[settings.mongo_db]
sessions = db.sessions

# WhatsApp link generator
def generate_whatsapp_link(phone_number: str):
    return f"https://wa.me/{phone_number}"

# Save user or bot message to session
async def save_session_message(session_id: str, text, sender: str):
    # Serialize AIMessage if necessary
    if isinstance(text, AIMessage):
        text = text.content

    await sessions.update_one(
        {"session_id": session_id},
        {
            "$push": {
                "messages": {
                    "sender": sender,
                    "text": text,
                    "timestamp": datetime.utcnow()
                }
            },
            "$setOnInsert": {"session_id": session_id}
        },
        upsert=True
    )

# Get full session
async def get_session_messages(session_id: str):
    doc = await sessions.find_one({"session_id": session_id})
    return doc.get("messages", []) if doc else []

# Handle handoff request: just return the WhatsApp link, no save
async def handle_bot_handoff(session_id: str):
    # Fetch entire session and save to archive collection if needed
    session_data = await get_session_messages(session_id)

    if session_data:
        # Optional: Save to a separate archived_sessions collection
        await db.archived_sessions.insert_one({
            "session_id": session_id,
            "messages": session_data,
            "handoff_time": datetime.utcnow()
        })

    # Respond with WhatsApp link only, no saving
    support_number = "1234567890"  
    whatsapp_link = generate_whatsapp_link(support_number)

    return f"Thanks! Here's the link to chat with a human agent on WhatsApp:\n\n{whatsapp_link}"
