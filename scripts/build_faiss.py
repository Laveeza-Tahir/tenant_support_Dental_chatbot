import json
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from config.settings import settings

def main():
    with open("data/dental_faqs.json", "r", encoding="utf-8") as f:
        faqs = json.load(f)

    texts = [f["question"] + "\n" + f["answer"] for f in faqs]
    metas = [{"source": f.get("source", "dental_faqs.json")} for f in faqs]

    emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    store = FAISS.from_texts(texts, emb, metadatas=metas)
    store.save_local(settings.faiss_index_path)
    print("✅ FAISS index built at", settings.faiss_index_path)

if __name__ == "__main__":
    main()
