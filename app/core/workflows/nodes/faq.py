from langgraph.graph import state
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.retrievers.chroma_retriever import ChromaRetriever
from config.settings import settings

class FAQNode:
    def __init__(self, k:int = 3):
        self.chroma_retriever = ChromaRetriever(k=k)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.google_api_key,
            temperature=0.3
        )
        
        self.prompt = ChatPromptTemplate.from_template("""
            You are a clinical assistant. Use *only* this context to answer:
            {context}

            Question: {query}

            Instructions:
            1. Use ONLY information from the provided documents to answer.
            2. Respond in **at most 2-3 sentences**.
            3. If the question cannot be answered using the provided context, clearly state that you don't have that specific information.
            4. Focus on dental-related information only.
            """)

    async def __call__(self, state: state) -> state:
        query = state["user_message"]
        user_id = state.get("user_id")
        
        if not user_id:
            state["final_response"] = "I apologize, but I need your user ID to access your dental clinic's specific information. Please try again or contact support."
            return state
            
        try:
            # Get documents from ChromaDB
            docs = self.chroma_retriever.retrieve(query, user_id)
            print(f"Retrieved {len(docs)} documents from ChromaDB for user {user_id}")
            
            if not docs:
                state["final_response"] = "I don't have any relevant information from your dental clinic's documents to answer that question. Please contact your dental office directly for specific information."
                return state
            
            # Format context with source attribution
            context_entries = []
            for i, d in enumerate(docs):
                entry = f"{i+1}. {d.page_content}"
                entry += f"  [Source: {d.metadata.get('source', 'Clinic FAQ')}]"
                context_entries.append(entry)
                
            context = "\n\n".join(context_entries)
            
            # Generate response using LLM
            chain = self.prompt | self.llm
            llm_out = await chain.ainvoke({"query": query, "context": context})
            answer = llm_out.content if hasattr(llm_out, "content") else str(llm_out)
            
            # Update state with response and sources
            state["final_response"] = answer.strip()
            state["retrieved_sources"] = [{
                "source": d.metadata.get("source", "Clinic FAQ"),
                "relevance_rank": i + 1,
                "distance": d.metadata.get("distance", None)
            } for i, d in enumerate(docs)]
            
            return state
            
        except Exception as e:
            print(f"Error in FAQNode: {e}")
            state["final_response"] = "I encountered an error while trying to access your clinic's information. Please try again later or contact support."
            return state
