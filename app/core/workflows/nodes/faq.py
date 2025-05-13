from langgraph.graph import state
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.retrievers.faiss_retriever import GeminiFAISSRetriever
from config.settings import settings
import logging
import re

class FAQNode:
    def __init__(self, k:int = 5):  # Increased k for better retrieval
        self.retriever = GeminiFAISSRetriever(k=k)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.google_api_key,
            temperature=0.3
        )
        # Improved prompt for better dental assistant responses
        self.prompt = ChatPromptTemplate.from_template(
            """
            You are a friendly and knowledgeable dental assistant. Use the following context to answer the patient's question. If the context doesn't contain relevant information, politely say you don't have that specific information instead of making things up.

            Context:
            {context}

            Patient Question: {query}

            Instructions:
            1. Answer clearly and directly in a conversational tone
            2. Use 2-3 sentences maximum for your response
            3. Include emoji when appropriate to make the response friendly
            4. If citing information, include [Source] at the end of the statement
            5. If asked about location, office hours, or contact details, politely redirect to the contact info section
            """
        )
        # Cache for common questions to improve performance
        self.response_cache = {}

    async def __call__(self, state: state) -> state:
        query = state["user_message"].lower().strip()
        
        # Check if we have a cached response
        if query in self.response_cache:
            logging.info(f"Using cached response for: '{query}'")
            state["final_response"] = self.response_cache[query]["response"]
            state["retrieved_sources"] = self.response_cache[query]["sources"]
            return state
        
        # Double-check for location-related terms
        location_terms = ["location", "address", "where", "office", "directions", "clinic", "map"]
        if any(term in query for term in location_terms):
            # This is a location query that somehow reached the FAQ node
            logging.warning(f"Location query detected in FAQ node: '{query}'. Changing intent to contact_info.")
            state["intent"] = "contact_info"
            # Don't process further in this node
            return state
        
        try:
            # Retrieve relevant documents
            docs = self.retriever.retrieve(query)
            
            if not docs:
                # No relevant documents found
                state["final_response"] = "I don't have specific information on that topic in my dental knowledge base. 🦷 Is there something else about dental care I can help with?"
                state["retrieved_sources"] = []
                return state
                
            # Format context with better numbering and source attribution
            context = "\n\n".join(
                f"Information {i+1}: {d.page_content}  [Source: {d.metadata.get('source','unknown')}]"
                for i, d in enumerate(docs)
            )
            
            # Generate response using LLM
            chain = self.prompt | self.llm
            llm_out = await chain.ainvoke({"query": query, "context": context})
            answer = llm_out.content if hasattr(llm_out, "content") else str(llm_out)
            
            # Process the answer to ensure source attribution is properly formatted
            processed_answer = self._format_answer(answer)
            
            # Store in state
            state["final_response"] = processed_answer
            state["retrieved_sources"] = [d.metadata.get("source", "unknown") for d in docs if d.metadata.get("source")]
            
            # Cache the response for future use
            self.response_cache[query] = {
                "response": processed_answer,
                "sources": state["retrieved_sources"]
            }
            
            # Limit cache size to prevent memory issues
            if len(self.response_cache) > 100:
                # Remove a random item
                self.response_cache.pop(next(iter(self.response_cache)))
                
        except Exception as e:
            # Handle any errors gracefully
            logging.error(f"Error in FAQ node: {str(e)}")
            state["final_response"] = "I apologize, but I'm having trouble retrieving that dental information right now. 🦷 Is there something else I can help with?"
            state["retrieved_sources"] = []
            
        return state
    
    def _format_answer(self, answer):
        """Format the answer to ensure proper source attribution and readability."""
        # Remove duplicate source tags
        answer = re.sub(r'\[Source\]\s*\[Source\]', '[Source]', answer)
        
        # Ensure source tags are properly formatted
        answer = re.sub(r'\[source\]', '[Source]', answer, flags=re.IGNORECASE)
        
        # Add a dental emoji if there isn't one
        if not any(emoji in answer for emoji in ["🦷", "😁", "🪥", "🧼"]):
            answer += " 🦷"
            
        return answer.strip()
