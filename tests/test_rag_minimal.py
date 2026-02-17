import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv()

from app.services.rag import rag_service

def test_rag():
    print("Initializing RAG...")
    # This should trigger initialization and save the index
    print(f"Docs Dir exists: {os.path.exists('data/company_docs')}")
    
    query = "What is the refund policy?"
    print(f"Querying: {query}")
    rag_service.reindex() # Force rebuild
    result = rag_service.query(query)
    print(f"Result: {result}")
    
    if "Refund Policy" in result:
        print("RAG Test Passed")
    else:
        print("RAG Test Failed")

if __name__ == "__main__":
    test_rag()
