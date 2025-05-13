from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import logging

from fastapi import HTTPException, status

from app.models.conversation import (
    ConversationInDB, ConversationCreate, Message, MessageSender,
    ConversationStatus, ChatRequest, ChatResponse
)
from app.db.database import DatabaseService
from app.langgraph.langgraph_service import LangGraphService
from app.services.bot_service import BotService

class ConversationService:
    """Service for managing conversations"""
    
    @staticmethod
    async def create_conversation(conversation_data: ConversationCreate) -> ConversationInDB:
        """Create a new conversation"""
        # Get bot to verify it exists
        bot = await BotService.get_bot(conversation_data.tenant_id, conversation_data.bot_id)
        if not bot:
            raise ValueError(f"Bot {conversation_data.bot_id} not found")
            
        # Create conversation ID
        conversation_id = str(uuid.uuid4())
        
        # Create a welcome message if the bot has one
        messages = []
        welcome_message = bot.settings.get("welcome_message") if bot.settings else None
        if welcome_message:
            messages.append(
                Message(
                    content=welcome_message,
                    sender=MessageSender.BOT
                )
            )
            
        # Create conversation record
        conversation = ConversationInDB(
            id=conversation_id,
            tenant_id=conversation_data.tenant_id,
            bot_id=conversation_data.bot_id,
            user_id=conversation_data.user_id,
            status=ConversationStatus.ACTIVE,
            messages=messages,
            session_data=conversation_data.session_data or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Get tenant-specific database
        tenant_db = DatabaseService.get_tenant_db(conversation_data.tenant_id)
        
        # Insert conversation
        await tenant_db.conversations.insert_one(conversation.dict())
        
        return conversation
        
    @staticmethod
    async def get_conversation(tenant_id: str, conversation_id: str) -> Optional[ConversationInDB]:
        """Get a conversation by ID"""
        # Get tenant-specific database
        tenant_db = DatabaseService.get_tenant_db(tenant_id)
        
        # Find conversation
        conversation_doc = await tenant_db.conversations.find_one({"id": conversation_id})
        if not conversation_doc:
            return None
            
        return ConversationInDB(**conversation_doc)
        
    @staticmethod
    async def list_conversations(
        tenant_id: str, 
        bot_id: Optional[str] = None, 
        user_id: Optional[str] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List conversations"""
        # Get tenant-specific database
        tenant_db = DatabaseService.get_tenant_db(tenant_id)
        
        # Build query
        query = {"tenant_id": tenant_id}
        if bot_id:
            query["bot_id"] = bot_id
        if user_id:
            query["user_id"] = user_id
            
        # Query conversations
        conversations = await tenant_db.conversations.find(query) \
                                              .sort("updated_at", -1) \
                                              .skip(skip) \
                                              .limit(limit) \
                                              .to_list(length=limit)
                                              
        return conversations
        
    @staticmethod
    async def add_message(
        tenant_id: str, 
        conversation_id: str, 
        content: str, 
        sender: MessageSender,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Add a message to a conversation"""
        # Create message
        message = Message(
            content=content,
            sender=sender,
            metadata=metadata
        )
        
        # Get tenant-specific database
        tenant_db = DatabaseService.get_tenant_db(tenant_id)
        
        # Add message to conversation
        await tenant_db.conversations.update_one(
            {"id": conversation_id},
            {
                "$push": {"messages": message.dict()},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return message
        
    @staticmethod
    async def process_chat_message(chat_request: ChatRequest, knowledge_base: List[Dict[str, Any]]) -> ChatResponse:
        """Process a chat message"""
        tenant_id = chat_request.tenant_id
        bot_id = chat_request.bot_id
        message = chat_request.message

        logging.info(f"Processing chat message for tenant_id={tenant_id}, bot_id={bot_id}, conversation_id={chat_request.conversation_id}")

        try:
            # Get or create conversation
            conversation = None
            if chat_request.conversation_id:
                conversation = await ConversationService.get_conversation(
                    tenant_id, 
                    chat_request.conversation_id
                )

            if not conversation:
                # Create new conversation
                conversation = await ConversationService.create_conversation(
                    ConversationCreate(
                        tenant_id=tenant_id,
                        bot_id=bot_id,
                        user_id=None,  # Removed reference to `chat_request.user_id` since it no longer exists
                        session_data={}
                    )
                )

            # Add user message to conversation
            await ConversationService.add_message(
                tenant_id=tenant_id,
                conversation_id=conversation.id,
                content=message,
                sender=MessageSender.USER
            )

            # Get updated conversation
            conversation = await ConversationService.get_conversation(
                tenant_id, 
                conversation.id
            )

            # Process message with LangGraph
            langgraph_service = LangGraphService(tenant_id, bot_id, knowledge_base=knowledge_base) # Pass knowledge_base
            result = await langgraph_service.run_graph(conversation, message)

            # Extract response
            bot_response = result["final_response"]["response"]
            sources = result["final_response"]["sources"]
            session_data = result["final_response"]["session_data"]

            # Add bot message to conversation
            await ConversationService.add_message(
                tenant_id=tenant_id,
                conversation_id=conversation.id,
                content=bot_response,
                sender=MessageSender.BOT,
                metadata={"sources": sources}
            )

            # Update session data if needed
            if session_data and session_data != conversation.session_data:
                tenant_db = DatabaseService.get_tenant_db(tenant_id)
                await tenant_db.conversations.update_one(
                    {"id": conversation.id},
                    {"$set": {"session_data": session_data}}
                )

            # Return chat response
            return ChatResponse(
                conversation_id=conversation.id,
                response=bot_response,
                sources=sources,
                session_data=session_data
            )

        except Exception as e:
            logging.error(f"Error processing chat message: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing chat message"
            )
