import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.services.rag import rag_service

async def test_rag():
    print("Initializing RAG Service...")
    await rag_service.initialize_vector_store()
    
    queries = [
        "How many annual leaves?",
        "Who are the directors?",
        "What is the salary payment date?"
    ]
    
    for q in queries:
        print(f"\n--- Query: {q} ---")
        result = await rag_service.query(q)
        print(result)

if __name__ == "__main__":
    asyncio.run(test_rag())
