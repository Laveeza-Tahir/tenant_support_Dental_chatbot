from langgraph.graph import state
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.retrievers.faiss_retriever import GeminiFAISSRetriever
from config.settings import settings

class FAQNode:
    def __init__(self, k:int = 3):
        self.retriever = GeminiFAISSRetriever(k=k)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.google_api_key,
            temperature=0.3
        )
        self.prompt = ChatPromptTemplate.from_template(
            """
            You are a dental assistant. Use *only* this context to answer:
            {context}

            Question: {query}

            Respond in **at most 2 sentences** and append [Source] after each fact.
            """
        )

    async def __call__(self, state: state) -> state:
        query = state["user_message"]
        docs = self.retriever.retrieve(query)
        context = "\n\n".join(
            f"{i+1}. {d.page_content}  [Source: {d.metadata.get('source','n/a')}]"
            for i, d in enumerate(docs)
        )
        chain = self.prompt | self.llm
        llm_out = await chain.ainvoke({"query": query, "context": context})
        answer = llm_out.content if hasattr(llm_out, "content") else str(llm_out)
        state["final_response"] = answer.strip()
        state["retrieved_sources"] = [d.metadata.get("source") for d in docs]
        return state
