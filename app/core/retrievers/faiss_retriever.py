from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings  # Use updated import

from config.settings import settings

class GeminiFAISSRetriever:
    def __init__(self, k: int = 3):
        self.k = k
        self.emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.store = FAISS.load_local(
            settings.faiss_index_path,
            self.emb,
            allow_dangerous_deserialization=True  # <-- this enables pickle loading
        )

    def retrieve(self, query: str):
        return self.store.similarity_search(query, k=self.k)
