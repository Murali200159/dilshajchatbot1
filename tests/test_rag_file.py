import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.services.rag import rag_service

async def test_rag():
    await rag_service.initialize_vector_store()
    
    queries = [
        "How many annual leaves?",
        "Who are the directors?",
        "What is the salary payment date?"
    ]
    
    with open("rag_test_results.txt", "w", encoding="utf-8") as f:
        for q in queries:
            f.write(f"\n--- Query: {q} ---\n")
            result = await rag_service.query(q)
            f.write(result + "\n")

if __name__ == "__main__":
    asyncio.run(test_rag())
