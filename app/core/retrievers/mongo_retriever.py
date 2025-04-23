from app.models.faq import FAQ
from app.models.session import db

class MongoFAQRetriever:
    async def retrieve(self, query: str):
        docs = await db.faqs.find().to_list(length=3)
        return [FAQ(**d) for d in docs]
