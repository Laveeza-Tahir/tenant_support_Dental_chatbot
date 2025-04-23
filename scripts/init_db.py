import json
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
import asyncio

async def main():
    client = AsyncIOMotorClient(settings.mongo_uri)
    db = client[settings.mongo_db]

    with open("data/dental_faqs.json") as f:
        faqs = json.load(f)
    await db.faqs.delete_many({})
    await db.faqs.insert_many(faqs)
    print("Initialized MongoDB with FAQs.")

if __name__ == "__main__":
    asyncio.run(main())
