"""
Debug script to check ChromaDB query results structure
"""

import os
import sys
import json

# Add the project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from app.core.chroma_manager import (
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
    create_or_update_collection("test_debug", test_faq)
    
    # Query the collection
    results = query_collection("test_debug", "How do I create a collection?")
    
    # Print the results structure
    print("\n--- Results Keys ---")
    print(f"Available keys in results: {list(results.keys())}")
    
    print("\n--- Results Types ---")
    for key, value in results.items():
        print(f"{key}: {type(value)}")
        if isinstance(value, list):
            print(f"  Length: {len(value)}")
            if len(value) > 0:
                print(f"  First item type: {type(value[0])}")
                if isinstance(value[0], list):
                    print(f"    Inner list length: {len(value[0])}")
                    if len(value[0]) > 0:
                        print(f"    Inner item type: {type(value[0][0])}")
    
    print("\n--- Sample Data ---")
    print(json.dumps(results, indent=2, default=str))
    
    print("\nDebug complete.")

if __name__ == "__main__":
    main()
