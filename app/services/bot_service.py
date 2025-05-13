from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import logging
import asyncio

from app.models.bot import (
    BotCreate, BotUpdate, BotInDB, BotResponse, 
    BotStatus, BotStatistics
)
from app.db.database import bots_collection
from app.db.database import DatabaseService
from app.vector_store.vector_db_service import VectorDBService

class BotService:
    """Service for managing bots"""
    
    @staticmethod
    async def create_bot(bot_data: BotCreate) -> BotResponse:
        """Create a new bot"""
        global bots_collection
        if bots_collection is None:
            logging.warning("bots_collection is None. Reinitializing database.")
            await DatabaseService.initialize()
            bots_collection = await DatabaseService.get_collection("bots")
            if bots_collection is None:
                raise ValueError("Failed to initialize bots_collection after reinitialization.")

        # Proceed with checking for existing bot
        existing_bot = await bots_collection.find_one({
            "tenant_id": bot_data.tenant_id,
            "name": bot_data.name
        })
        
        if existing_bot:
            raise ValueError(f"Bot with name '{bot_data.name}' already exists for this tenant")
            
        # Generate bot ID
        bot_id = str(uuid.uuid4())
        
        # Create bot data
        bot = BotInDB(
            id=bot_id,
            name=bot_data.name,
            description=bot_data.description,
            tenant_id=bot_data.tenant_id,
            bot_type=bot_data.bot_type,
            engine=bot_data.engine,
            custom_instructions=bot_data.custom_instructions,
            settings=bot_data.settings or {},
            status=BotStatus.CREATING,  # Start in creating status
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Insert into database
        await bots_collection.insert_one(bot.dict())
        
        # Initialize vector DB collection in background
        asyncio.create_task(BotService._initialize_bot_vectordb(bot))
        
        return BotResponse(**bot.dict())
        
    @staticmethod
    async def _initialize_bot_vectordb(bot: BotInDB):
        """Initialize the vector database for this bot"""
        try:
            # Set bot to READY status
            await bots_collection.update_one(
                {"id": bot.id},
                {
                    "$set": {
                        "status": BotStatus.READY,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        except Exception as e:
            # Set error status
            logging.error(f"Error initializing bot {bot.id}: {e}")
            await bots_collection.update_one(
                {"id": bot.id},
                {
                    "$set": {
                        "status": BotStatus.ERROR,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
    
    @staticmethod
    async def get_bot(tenant_id: str, bot_id: str) -> Optional[BotInDB]:
        """Get a bot by ID"""
        global bots_collection
        if bots_collection is None:
            logging.warning("bots_collection is None. Reinitializing database.")
            await DatabaseService.initialize()
            bots_collection = await DatabaseService.get_collection("bots")
            if bots_collection is None:
                raise ValueError("Failed to initialize bots_collection after reinitialization.")

        bot_doc = await bots_collection.find_one({
            "tenant_id": tenant_id,
            "id": bot_id
        })
        
        if not bot_doc:
            return None
            
        return BotInDB(**bot_doc)
        
    @staticmethod
    async def update_bot(tenant_id: str, bot_id: str, bot_data: BotUpdate) -> Optional[BotResponse]:
        """Update a bot"""
        # Check if bot exists
        bot = await BotService.get_bot(tenant_id, bot_id)
        if not bot:
            return None
            
        # Create update data
        update_data = {k: v for k, v in bot_data.dict(exclude_unset=True).items() if v is not None}
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            update_data["status"] = BotStatus.UPDATING  # Set to updating status
            
            # Update bot
            await bots_collection.update_one(
                {"id": bot_id, "tenant_id": tenant_id},
                {"$set": update_data}
            )
            
            # Get updated bot
            updated_bot = await BotService.get_bot(tenant_id, bot_id)
            
            # Set back to READY in background
            asyncio.create_task(BotService._set_bot_ready(tenant_id, bot_id))
            
            return BotResponse(**updated_bot.dict())
        
        return BotResponse(**bot.dict())
    
    @staticmethod
    async def _set_bot_ready(tenant_id: str, bot_id: str):
        """Set bot status back to READY after a short delay"""
        # Wait a short time to simulate processing
        await asyncio.sleep(2)
        
        # Set status to READY
        await bots_collection.update_one(
            {"id": bot_id, "tenant_id": tenant_id},
            {
                "$set": {
                    "status": BotStatus.READY,
                    "updated_at": datetime.utcnow(),
                    "last_trained_at": datetime.utcnow()
                }
            }
        )
        
    @staticmethod
    async def list_bots(tenant_id: str, skip: int = 0, limit: int = 100) -> List[BotResponse]:
        """List all bots for a tenant"""
        global bots_collection
        if bots_collection is None:
            logging.warning("bots_collection is None. Reinitializing database.")
            await DatabaseService.initialize()
            bots_collection = await DatabaseService.get_collection("bots")
            if bots_collection is None:
                raise ValueError("Failed to initialize bots_collection after reinitialization.")

        cursor = (
            bots_collection.find({"tenant_id": tenant_id})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        
        bots = await cursor.to_list(length=limit)
        return [BotResponse(**bot) for bot in bots]
        
    @staticmethod
    async def delete_bot(tenant_id: str, bot_id: str) -> bool:
        """Delete a bot"""
        # Check if bot exists
        bot = await BotService.get_bot(tenant_id, bot_id)
        if not bot:
            return False
            
        # Delete from database
        result = await bots_collection.delete_one({
            "id": bot_id,
            "tenant_id": tenant_id
        })
        
        # Delete vector database for this bot
        # This would be a more complex operation in a real system,
        # potentially deleting only the specific collection for this bot
        
        return result.deleted_count > 0
        
    @staticmethod
    async def get_bot_statistics(tenant_id: str, bot_id: str) -> BotStatistics:
        """Get usage statistics for a bot"""
        # This would typically involve querying the conversation history,
        # calculating metrics, etc.
        
        # For now, return a simple placeholder
        return BotStatistics(
            total_messages=0,
            total_conversations=0,
            avg_user_rating=None,
            last_active=None
        )
