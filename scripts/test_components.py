
import asyncio
import httpx
import uuid
import json
from app.core.config import settings

async def test_all_components():
    print("\n--- Starting Comprehensive Component Check ---\n")
    
    # 1. Check MongoDB (via service)
    print("1. Testing MongoDB...")
    try:
        from app.services.database import database_service
        db_healthy = await database_service.health_check()
        if db_healthy and not database_service.is_mock:
            print("✅ MongoDB: Connected and Healthy")
            # Try a simple insertion and deletion to confirm write access
            test_user = await database_service.create_user(f"test_{uuid.uuid4()}@example.com", "password")
            if test_user:
                print("✅ MongoDB: Write access verified")
                await database_service.delete_user_by_email(test_user['email'])
        elif database_service.is_mock:
            print("⚠️  MongoDB: Running in MOCK MODE (Check if MongoDB is started on port 27017)")
        else:
            print("❌ MongoDB: Unhealthy")
    except Exception as e:
        print(f"❌ MongoDB: Error - {e}")

    # 2. Check Ollama (LLM Provider)
    print("\n2. Testing Ollama Connection...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.LLM_BASE_URL.rstrip('/')}/api/tags")
            if resp.status_code == 200:
                models = resp.json().get('models', [])
                model_names = [m['name'] for m in models]
                print(f"✅ Ollama: Accessible. Available models: {', '.join(model_names)}")
                
                # Check for specific models used in .env
                required_models = [settings.DEFAULT_LLM_MODEL, os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")]
                for rm in required_models:
                    if any(rm in m for m in model_names):
                        print(f"✅ Ollama: Model '{rm}' is ready")
                    else:
                        print(f"❌ Ollama: Model '{rm}' NOT found. Please run 'ollama pull {rm}'")
            else:
                print(f"❌ Ollama: Accessible but returned status {resp.status_code}")
    except Exception as e:
        print(f"❌ Ollama: Not reachable at {settings.LLM_BASE_URL}. Error: {e}")

    # 3. Check RAG Service
    print("\n3. Testing RAG (Vector Store)...")
    try:
        from app.services.rag import rag_service
        # Test a simple query
        result = await rag_service.query("What is Dilshaj Infotech?")
        if "Internal Error" in result:
            print(f"❌ RAG: Service returned error - {result}")
        elif "No matching information" in result:
            print("⚠️  RAG: Knowledge base empty or no match found (Check data/company_docs/*.md)")
        else:
            print("✅ RAG: Query successful. Knowledge retrieval working.")
            print(f"   (Preview: {result[:100]}...)")
    except Exception as e:
        print(f"❌ RAG: Error - {e}")

    # 4. Check LLM Service (Actual inference)
    print("\n4. Testing LLM Inference (llama3.1)...")
    try:
        from app.services.llm import llm_service
        response = await llm_service.chat([{"role": "user", "content": "Hi, just say 'LLM is working' if you hear me."}])
        if response:
            print(f"✅ LLM: Chat successful. Response: '{response}'")
        else:
            print("❌ LLM: Chat returned empty response")
    except Exception as e:
        print(f"❌ LLM: Inference failed - {e}")

    print("\n--- Verification Complete ---\n")

if __name__ == "__main__":
    import os
    import sys
    # Ensure app is in path
    sys.path.append(os.getcwd())
    asyncio.run(test_all_components())
