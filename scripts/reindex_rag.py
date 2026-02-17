import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.services.rag import rag_service

async def reindex():
    print("Triggering RAG Reindex...")
    result = await rag_service.reindex()
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(reindex())
