from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config.settings import settings
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

class DatabaseService:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None
    
    @classmethod
    async def initialize(cls):
        """Initialize database connection"""
        if cls.client is None:
            try:
                cls.client = AsyncIOMotorClient(settings.mongo_uri)
                cls.db = cls.client[settings.mongo_db]
                logging.info(f"Connected to MongoDB: {settings.mongo_db}")
            except Exception as e:
                logging.error(f"Failed to connect to MongoDB: {e}")
                raise
    
    @classmethod
    async def close(cls):
        """Close database connection"""
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.db = None
            logging.info("Closed MongoDB connection")
    
    @classmethod
    async def get_collection(cls, collection_name: str):
        """Get a collection with the specific name"""
        if cls.db is None:
            await cls.initialize()
        return cls.db[collection_name]
    
    @classmethod
    def get_tenant_db_name(cls, tenant_id: str) -> str:
        """Get database name for a specific tenant"""
        truncated_tenant_id = tenant_id[:30]  # Truncate tenant ID to 30 characters
        return f"{settings.mongo_db}_tenant_{truncated_tenant_id}"
    
    @classmethod
    def get_tenant_db(cls, tenant_id: str) -> AsyncIOMotorDatabase:
        """Get database for a specific tenant"""
        if cls.client is None:
            raise ValueError("Database client not initialized")
        return cls.client[cls.get_tenant_db_name(tenant_id)]

# Global collections
tenants_collection = None
users_collection = None
bots_collection = None
files_collection = None

async def init_db():
    """Initialize database and global collections"""
    logging.info("Starting database initialization...")
    await DatabaseService.initialize()

    global tenants_collection, users_collection, bots_collection, files_collection

    tenants_collection = await DatabaseService.get_collection("tenants")
    if tenants_collection is None:
        logging.error("Failed to initialize tenants_collection")

    users_collection = await DatabaseService.get_collection("users")
    bots_collection = await DatabaseService.get_collection("bots")
    files_collection = await DatabaseService.get_collection("files")

    logging.info("Initializing global collections...")
    logging.info("tenants_collection initialized: %s", tenants_collection is not None)
    logging.info("users_collection initialized: %s", users_collection is not None)
    logging.info("bots_collection initialized: %s", bots_collection is not None)
    logging.info("files_collection initialized: %s", files_collection is not None)

    logging.info("Database initialization completed.")