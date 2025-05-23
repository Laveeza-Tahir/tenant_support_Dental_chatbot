"""
Debug script to diagnose ChromaDB issues.
This script will:
1. List existing collections
2. Create a test collection
3. Query the test collection
"""

import os
import sys
import chromadb

# Add the project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from app.core.chroma_manager import (
    chroma_client, 
    create_or_update_collection, 
    query_collection, 
    list_all_collections,
    split_faq_to_documents
)

def main():
    print("\n========== ChromaDB Debug Tool ==========\n")
    
    # Print ChromaDB client info
    print(f"ChromaDB Client Type: {type(chroma_client)}")
    
    # Check for persistence attributes in different ways since the API might vary
    if hasattr(chroma_client, "_path"):
        print(f"Persistence Directory: {chroma_client._path}")
    elif hasattr(chroma_client, "path"):
        print(f"Persistence Directory: {chroma_client.path}")
    elif hasattr(chroma_client, "__class__") and "PersistentClient" in str(chroma_client.__class__):
        print(f"Using PersistentClient (should be saving to disk)")
    else:
        print("Persistence Directory: None (In-Memory)")
        
    # Check if directory exists
    if os.path.exists("d:/Dental_chatbot_calendly - Copy/chroma_db"):
        print(f"Chroma DB directory exists: {os.listdir('d:/Dental_chatbot_calendly - Copy/chroma_db')}")
    
    # Check regex pattern
    print("\n--- Testing Regex Pattern ---")
    test_qa = "Q: This is a test question?\nA: This is a test answer."
    docs = split_faq_to_documents(test_qa)
    print(f"Testing simple Q&A: {docs}")
    
    print("\n--- Existing Collections ---")
    collections = list_all_collections()
    if collections:
        for i, col in enumerate(collections, 1):
            print(f"{i}. {col}")
    else:
        print("No collections found.")
    
    print("\n--- Creating Test Collection ---")
    test_faq = """Q: What is this test?
A: This is a test collection for debugging ChromaDB issues.

Q: How do I create a collection?
A: Use the create_or_update_collection function.

Q: Why might collections not be persisting?
A: The client might be in-memory, or the path might be incorrect."""
    
    try:
        create_or_update_collection("test_debug", test_faq)
        print("✓ Test collection created successfully")
    except Exception as e:
        print(f"✗ Error creating test collection: {e}")
    
    print("\n--- Collections After Creation ---")
    collections_after = list_all_collections()
    if collections_after:
        for i, col in enumerate(collections_after, 1):
            print(f"{i}. {col}")
    else:
        print("No collections found.")
    
    print("\n--- Testing Query ---")
    try:
        results = query_collection("test_debug", "How do I create a collection?")
        print("✓ Query successful")
        print(f"Documents: {results['documents']}")
    except Exception as e:
        print(f"✗ Error querying test collection: {e}")
    
    print("\nDebug complete.")

if __name__ == "__main__":
    main()
