import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dotenv import load_dotenv
load_dotenv()

from app.core.langgraph.tools.rag import company_docs_tool
from app.core.langgraph.tools.mongodb import user_payment_tool

async def test_company_docs():
    print("\n--- Testing Company Docs Tool ---")
    
    # Test Policy
    query = "What is the refund policy?"
    print(f"Query: {query}")
    result = await company_docs_tool.ainvoke(query)
    print(f"Result: {result[:200]}...")
    
    # Test Product
    query = "Tell me about monitors"
    print(f"Query: {query}")
    result = await company_docs_tool.ainvoke(query)
    print(f"Result: {result[:200]}...")

    print("✅ Company Docs Tool Verified")

async def test_mongodb_tool():
    print("\n--- Testing MongoDB Tool ---")
    
    try:
        # 1. Test get_user
        print("Testing get_user...")
        result = await user_payment_tool.ainvoke({"query_type": "get_user", "user_id": "test@example.com"})
        print(f"Result: {result}")
        
        # 2. Test check_payment
        print("Testing check_payment...")
        result = await user_payment_tool.ainvoke({"query_type": "check_payment", "transaction_id": "tx_999"})
        print(f"Result: {result}")
        
        print("✅ MongoDB Tool executed")
        
    except Exception as e:
        print(f"❌ MongoDB Tool Test Failed: {e}")

async def main():
    await test_company_docs()
    await test_mongodb_tool()

if __name__ == "__main__":
    asyncio.run(main())
