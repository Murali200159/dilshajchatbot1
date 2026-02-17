
import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.core.langgraph.tools.mongodb import user_payment_tool
import logging
logging.getLogger().setLevel(logging.WARNING)

async def test_mongodb_tool():
    print("Testing user_payment_tool...")
    
    user_id = "sarip@dilshajinfotech.com"
    transaction_id = "TXN_1001"
    
    with open("test_mongo_output_encoded.txt", "w", encoding="utf-8") as f:
        # Test 1: Get User Details
        f.write("\n--- Test 1: Get User Details ---\n")
        result = await user_payment_tool.ainvoke({"query_type": "get_user", "user_id": user_id})
        f.write(result + "\n")
        
        # Test 2: Get Payment History
        f.write("\n--- Test 2: Get Payment History ---\n")
        result = await user_payment_tool.ainvoke({"query_type": "get_payment_history", "user_id": user_id})
        f.write(result + "\n")

        # Test 3: Check Payment Status
        f.write("\n--- Test 3: Check Payment Status ---\n")
        result = await user_payment_tool.ainvoke({"query_type": "check_payment", "transaction_id": transaction_id})
        f.write(result + "\n")

if __name__ == "__main__":
    asyncio.run(test_mongodb_tool())
