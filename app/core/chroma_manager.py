import os
import re
import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import EmbeddingFunction
from sentence_transformers import SentenceTransformer
from typing import List

# Initialize SentenceTransformer model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Custom embedding function compatible with ChromaDB
class CustomEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: list[str]):
        return embedding_model.encode(input, convert_to_tensor=False).tolist()

embedding_function = CustomEmbeddingFunction()

# Initialize Chroma client with persistent storage
persist_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chroma_db")
os.makedirs(persist_directory, exist_ok=True)
print(f"Initializing ChromaDB with persistence directory: {persist_directory}")
try:
    chroma_client = chromadb.PersistentClient(path=persist_directory)
    print(f"ChromaDB client initialized with persistence at {persist_directory}")
except Exception as e:
    print(f"Error creating persistent ChromaDB client: {e}")
    chroma_client = chromadb.Client()

def split_text_to_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split any text document into overlapping chunks for better semantic search."""
    # Clean the text by removing excessive whitespace
    cleaned_text = " ".join(text.split())
    
    # If the text is shorter than chunk_size, return it as a single chunk
    if len(cleaned_text) <= chunk_size:
        return [cleaned_text]
    
    chunks = []
    start = 0
    
    while start < len(cleaned_text):
        # Find the end of the chunk
        end = start + chunk_size
        
        # If this isn't the last chunk, try to break at a sentence boundary
        if end < len(cleaned_text):
            # Look for sentence boundaries (., !, ?) followed by a space
            sentence_end = -1
            for punct in [". ", "! ", "? "]:
                last_punct = cleaned_text[start:end].rfind(punct)
                if last_punct > sentence_end:
                    sentence_end = last_punct
            
            if sentence_end != -1:
                end = start + sentence_end + 2  # +2 to include the punctuation and space
        
        # Add the chunk to our list
        chunk = cleaned_text[start:end].strip()
        if chunk:  # Only add non-empty chunks
            chunks.append(chunk)
        
        # Move the start position, accounting for overlap
        start = end - overlap if end < len(cleaned_text) else end
    
    print(f"Split text into {len(chunks)} chunks")
    return chunks

def create_or_update_collection(user_id: str, raw_text: str):
    """Create or update a user-specific Chroma collection with document content."""
    collection_name = f"user_{user_id}"

    # Delete existing collection if it exists
    existing_collections = [col.name for col in chroma_client.list_collections()]
    if collection_name in existing_collections:
        chroma_client.delete_collection(name=collection_name)

    # Create a new collection
    collection = chroma_client.create_collection(
        name=collection_name,
        embedding_function=embedding_function
    )

    # Split text into chunks
    chunks = split_text_to_chunks(raw_text)
    if not chunks:
        raise ValueError("No valid text content found in the uploaded document.")

    # Add to collection
    collection.add(
        documents=chunks,
        metadatas=[{"user_id": user_id, "chunk_index": i} for i in range(len(chunks))],
        ids=[f"chunk_{i}" for i in range(len(chunks))]
    )

    return collection

def query_collection(user_id: str, query: str):
    """Query a user's Chroma collection for relevant FAQ answers."""
    collection_name = f"user_{user_id}"

    # Load collection
    try:
        collection = chroma_client.get_collection(name=collection_name)
    except Exception as e:
        raise RuntimeError(f"Collection not found for user '{user_id}'. Upload FAQs first.") from e

    # Perform semantic search
    results = collection.query(
        query_texts=[query],
        n_results=5
    )

    return results

def list_all_collections():
    """Utility function to list all collections in the ChromaDB database."""
    collections = chroma_client.list_collections()
    return [col.name for col in collections]
