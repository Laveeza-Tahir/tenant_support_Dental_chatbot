import sys
import os

# Add the workspace root directory to the Python module search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
import asyncio
from app.api.auth import Base, engine

async def main():
    client = AsyncIOMotorClient(settings.mongo_uri)
    db = client[settings.mongo_db]

    with open("data/dental_faqs.json") as f:
        faqs = json.load(f)
    await db.faqs.delete_many({})
    await db.faqs.insert_many(faqs)
    print("Initialized MongoDB with FAQs.")

# Initialize the database
def init_db():
    # Drop and recreate all tables to include the new `user_id` field
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    asyncio.run(main())
