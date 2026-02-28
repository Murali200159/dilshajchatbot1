import asyncio
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

async def check_health():
    print("--- Health Check Started ---")
    
    # Check MongoDB
    print("\n[1] Checking MongoDB...")
    try:
        from app.services.database import database_service
        # The service initializes on import. Let's trigger a check.
        is_mock = database_service.is_mock
        if is_mock:
            print("[WARNING] MongoDB is NOT reachable (Running in MOCK mode)")
        else:
            # Try a ping with short timeout
            try:
                # database_service.client.admin.command is a motor method, it's already async
                await asyncio.wait_for(database_service.client.admin.command("ping"), timeout=2.0)
                print("[SUCCESS] MongoDB is UP and REACHABLE")
            except Exception as e:
                print(f"[FAIL] MongoDB Ping Failed: {e}")
                print("[NOTE] This is normal if you haven't started 'docker compose up' yet.")
    except Exception as e:
        print(f"[ERROR] MongoDB Service Error: {e}")

    # Check RAG
    print("\n[2] Checking RAG Service...")
    try:
        from app.services.rag import rag_service
        if rag_service.vector_store is None:
            print("[WARNING] RAG Vector Store is NOT initialized")
            # Try to initialize it
            print("Attempting to initialize RAG Vector Store (loading docs)...")
            await asyncio.wait_for(rag_service.initialize_vector_store(), timeout=10.0)
            if rag_service.vector_store:
                print("[SUCCESS] RAG Vector Store initialized successfully")
            else:
                print("[FAIL] RAG Vector Store initialization failed (maybe no docs in data/company_docs?)")
        else:
            print(f"[SUCCESS] RAG Vector Store is UP (Ready for queries)")
            
        # Test a query
        if rag_service.vector_store:
            print("Testing RAG Query...")
            result = await rag_service.query("What is the company architecture?")
            if "Error" in result or "No matching" in result:
                print(f"[WARNING] RAG Query returned empty or error (this means it works but found nothing)")
            else:
                print("[SUCCESS] RAG Query successful! Content retrieved.")
    except Exception as e:
        print(f"[ERROR] RAG Service Error: {e}")

    print("\n--- Health Check Finished ---")

if __name__ == "__main__":
    asyncio.run(check_health())
