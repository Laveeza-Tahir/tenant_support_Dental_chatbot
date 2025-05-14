
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Dict, Any
import logging

async def llm_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate response using LLM"""
    messages = state["messages"]
    context = state["context"]
        
    # Create the prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful AI assistant. Use the following context to answer the question. 
If you don't know the answer based on the context, just say so - don't make things up.

Context: {context}"""),
        *[(msg.type, msg.content) for msg in messages]
    ])
        
    # Create the chain
    chain = prompt | self.llm | StrOutputParser()
        
    # Generate the response
    try:
        response = await chain.ainvoke({
            "context": context
        })
        state["response"] = response
    except Exception as e:
        logging.error(f"Error generating LLM response: {e}")
        state["response"] = "I'm sorry, I encountered an error while processing your request."
        
    return state
    