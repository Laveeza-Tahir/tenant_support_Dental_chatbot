from typing import Dict, Any, List, Optional, TypedDict  # Added TypedDict
from datetime import datetime
import logging
import uuid

from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage  # Added BaseMessage
from langchain_core.documents import Document  # Added Document
from langchain_google_genai import ChatGoogleGenerativeAI


from app.vector_store.vector_db_service import VectorDBService
from app.models.conversation import MessageSender, ConversationInDB
from config.settings import settings

from ..core.workflows.nodes.input_processor import input_processor
from ..core.workflows.nodes.llm_response import llm_response
from ..core.workflows.nodes.output_response import output_processor
from ..core.workflows.nodes.retrieval import retrieval


# Define the state schema for the graph
class GraphState(TypedDict):
    messages: List[BaseMessage]
    conversation_id: str
    tenant_id: str
    bot_id: str
    session_data: Dict[str, Any]
    docs: List[Document]
    user_query: Optional[str]
    context: Optional[str]
    response: Optional[str]
    sources: Optional[List[str]]
    final_response: Optional[Dict[str, Any]]

class LangGraphService:
    """LangGraph service for managing chatbot workflows"""
    
    def __init__(self, tenant_id: str, bot_id: str, knowledge_base: Optional[List[Dict[str, Any]]] = None):
        self.tenant_id = tenant_id
        self.bot_id = bot_id
        self.knowledge_base = knowledge_base  # Store knowledge_base
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.google_api_key,
            temperature=0.3
        )
        self.vector_db = VectorDBService(tenant_id, bot_id)
        
    def create_graph(
        self, 
        custom_instructions: Optional[str] = None, 
        system_instructions: Optional[str] = None
    ):
        """Create a LangGraph workflow for the chatbot"""
        # Define default system and custom instructions if not provided
        if not system_instructions:
            system_instructions = (
                "You are a helpful AI assistant. Use the provided documents "
                "to answer questions. If you don't know the answer, say so."
            )
            
        if custom_instructions:
            system_instructions = f"{system_instructions}\n\n{custom_instructions}"
            
        # Define the workflow using the TypedDict state schema
        workflow = StateGraph(GraphState)
        
        # Define workflow nodes
        workflow.add_node("input_processor", input_processor)
        workflow.add_node("retrieval", retrieval)
        workflow.add_node("llm_response", llm_response)
        workflow.add_node("output_processor", output_processor)
        
        # Connect the nodes
        workflow.set_entry_point("input_processor")
        workflow.add_edge("input_processor", "retrieval")
        workflow.add_edge("retrieval", "llm_response")
        workflow.add_edge("llm_response", "output_processor")
        workflow.add_edge("output_processor", END)
        
        # Compile the workflow
        return workflow.compile()
    
    async def run_graph(
        self, 
        conversation: ConversationInDB, 
        message: str
    ) -> Dict[str, Any]:
        """Run the graph workflow with a user message"""
        # Create initial state with conversation history and new message
        messages = []
        
        # Add existing conversation messages
        for conv_msg in conversation.messages:
            if conv_msg.sender == MessageSender.USER:
                messages.append(HumanMessage(content=conv_msg.content))
            elif conv_msg.sender == MessageSender.BOT:
                messages.append(AIMessage(content=conv_msg.content))
            elif conv_msg.sender == MessageSender.SYSTEM:
                messages.append(SystemMessage(content=conv_msg.content))
        
        # Add new user message
        messages.append(HumanMessage(content=message))
        
        # Define initial state
        state = {
            "messages": messages,
            "conversation_id": conversation.id,
            "tenant_id": self.tenant_id,
            "bot_id": self.bot_id,
            "session_data": conversation.session_data,
            "docs": []  # Will store retrieved docs
        }
        
        # Build the graph
        graph = self.create_graph()
        
        # Log the initial state for debugging
        logging.debug(f"Initial state before graph execution: {state}")

        # Execute the graph
        result = await graph.ainvoke(state)

        # Log the final state for debugging
        logging.debug(f"Final state after graph execution: {result}")
        
        # Return final state
        return result
    
    
    
    

