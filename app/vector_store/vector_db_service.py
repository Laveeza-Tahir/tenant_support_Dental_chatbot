import os
from typing import List, Dict, Any, Optional
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma, FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config.settings import settings
import logging
import uuid
import shutil

class VectorDBService:
    def __init__(self, tenant_id: str, bot_id: str):
        self.tenant_id = tenant_id
        self.bot_id = bot_id
        self.embed_model = HuggingFaceEmbeddings(
            model_name=settings.embeddings_model_name
        )
        self.tenant_chroma_path = os.path.join(
            settings.chroma_persist_directory, 
            f"tenant_{tenant_id}_bot_{bot_id}"
        )
        
        # Create directory if it doesn't exist
        os.makedirs(self.tenant_chroma_path, exist_ok=True)
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
    
    def get_db(self, collection_name: str = "default"):
        """Get ChromaDB instance for this tenant and bot"""
        return Chroma(
            collection_name=collection_name,
            embedding_function=self.embed_model,
            persist_directory=self.tenant_chroma_path
        )
        
    async def add_texts(
        self, 
        texts: List[str], 
        metadatas: List[Dict[str, Any]],
        collection_name: str = "default",
        ids: Optional[List[str]] = None
    ):
        """Add texts to the vector database"""
        # Split texts into chunks
        docs = []
        for i, text in enumerate(texts):
            chunks = self.text_splitter.split_text(text)
            # Add chunk index to metadata
            for j, chunk in enumerate(chunks):
                chunk_metadata = metadatas[i].copy() if metadatas and i < len(metadatas) else {}
                chunk_metadata["chunk"] = j
                docs.append(Document(page_content=chunk, metadata=chunk_metadata))
        
        # Generate IDs if not provided
        if not ids:
            ids = [str(uuid.uuid4()) for _ in range(len(docs))]
            
        # Store in the vector database
        db = self.get_db(collection_name)
        db.add_documents(docs, ids=ids)
        
        return {
            "added_count": len(docs),
            "collection": collection_name
        }
    
    async def search(
        self, 
        query: str, 
        collection_name: str = "default",
        k: int = 5, 
        filter: Optional[Dict[str, Any]] = None
    ):
        """Search the vector database with a query"""
        db = self.get_db(collection_name)
        results = db.similarity_search(
            query, 
            k=k,
            filter=filter
        )
        return results
        
    async def delete_collection(self, collection_name: str = "default"):
        """Delete a collection for this tenant"""
        try:
            db = self.get_db(collection_name)
            db.delete_collection()
            return True
        except Exception as e:
            logging.error(f"Error deleting collection {collection_name}: {e}")
            return False
            
    async def delete_by_ids(self, ids: List[str], collection_name: str = "default"):
        """Delete documents by IDs"""
        db = self.get_db(collection_name)
        db.delete(ids=ids)
        return len(ids)
        
    async def delete_by_filter(self, filter: Dict[str, Any], collection_name: str = "default"):
        """Delete documents by filter"""
        db = self.get_db(collection_name)
        # Get matching IDs first
        matches = db.get(filter=filter)
        if matches and matches['ids']:
            return await self.delete_by_ids(matches['ids'], collection_name)
        return 0
        
    async def purge_tenant_data(self):
        """Delete all vector data for this tenant - USE WITH CAUTION"""
        try:
            if os.path.exists(self.tenant_chroma_path):
                shutil.rmtree(self.tenant_chroma_path)
            return True
        except Exception as e:
            logging.error(f"Failed to purge tenant vector data: {e}")
            return False
