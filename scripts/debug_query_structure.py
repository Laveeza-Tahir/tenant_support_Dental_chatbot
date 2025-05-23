"""
Debug script to check ChromaDB query results structure
"""

import os
import sys
import json
import pprint

# Add the project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from app.core.chroma_manager import (
    chroma_client,
    create_or_update_collection, 
    query_collection
)

def main():
    print("\n========== ChromaDB Query Results Debug ==========\n")
    
    # Create a test collection
    test_faq = """Q: What is this test?
A: This is a test collection for debugging ChromaDB issues.

Q: How do I create a collection?
A: Use the create_or_update_collection function.

Q: Why might collections not be persisting?
A: The client might be in-memory, or the path might be incorrect."""
    
    # Create collection
    try:
        create_or_update_collection("test_debug", test_faq)
        print("✓ Test collection created successfully")
    except Exception as e:
        print(f"✗ Error creating test collection: {e}")
    
    # Query the collection
    try:
        results = query_collection("test_debug", "How do I create a collection?")
        print("✓ Query successful")
    except Exception as e:
        print(f"✗ Error querying collection: {e}")
        return
    
    # Print the results structure
    print("\n--- Results Keys ---")
    print(f"Available keys in results: {list(results.keys())}")
    
    print("\n--- Results Structure ---")
    for key, value in results.items():
        print(f"Key: {key}")
        print(f"Type: {type(value)}")
        if isinstance(value, list):
            print(f"List Length: {len(value)}")
            if len(value) > 0:
                print(f"First item type: {type(value[0])}")
                print(f"First item: {value[0]}")
                
    print("\n--- Recommended Access Pattern ---")
    print("Based on structure, here's how to access documents:")
    
    # Try different access patterns
    try:
        if 'documents' in results and len(results['documents']) > 0:
            # Handle the case where documents is a list of documents
            if isinstance(results['documents'][0], list):
                print(f"Pattern 1 (documents[0][0]): {results['documents'][0][0]}")
            # Handle the case where documents is a list containing one list of documents
            else:
                print(f"Pattern 2 (documents[0]): {results['documents'][0]}")
    except Exception as e:
        print(f"Error accessing documents: {e}")
    
    print("\n--- Full Results ---")
    pprint.pprint(results)
    
    print("\nDebug complete.")

if __name__ == "__main__":
    main()
