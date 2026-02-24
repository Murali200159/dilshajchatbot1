import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def check_mongo():
    uri = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
    print(f"Checking MongoDB at {uri}...")
    try:
        client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=2000)
        await client.admin.command('ping')
        print("✅ MongoDB is reachable!")
    except Exception as e:
        print(f"❌ MongoDB is NOT reachable: {e}")

if __name__ == "__main__":
    asyncio.run(check_mongo())
