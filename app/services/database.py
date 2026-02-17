"""
MongoDB database service for the application.
Replaces PostgreSQL + SQLModel with MongoDB (Motor async driver).
"""

from typing import List, Optional
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from app.core.config import settings
from app.core.logging import logger


class DatabaseService:
    """Service class for MongoDB operations.

    Handles Users and Chat Sessions using MongoDB.
    """

    def __init__(self):
        try:
            self.client = AsyncIOMotorClient(settings.MONGO_URI)
            self.db = self.client[settings.MONGO_DB_NAME]

            self.users = self.db["users"]
            self.sessions = self.db["sessions"]

            logger.info(
                "mongo_database_initialized",
                environment=settings.ENVIRONMENT.value,
            )

        except Exception as e:
            logger.error("mongo_initialization_error", error=str(e))
            raise

    # ----------------------------
    # USER OPERATIONS
    # ----------------------------

    async def create_user(self, email: str, password: str) -> dict:
        user = {
            "email": email,
            "hashed_password": password,
        }
        result = await self.users.insert_one(user)
        user["_id"] = str(result.inserted_id)
        logger.info("user_created", email=email)
        return user

    async def get_user(self, user_id: str) -> Optional[dict]:
        user = await self.users.find_one({"_id": ObjectId(user_id)})
        if user:
            user["_id"] = str(user["_id"])
        return user

    async def get_user_by_email(self, email: str) -> Optional[dict]:
        user = await self.users.find_one({"email": email})
        if user:
            user["_id"] = str(user["_id"])
        return user

    async def delete_user_by_email(self, email: str) -> bool:
        result = await self.users.delete_one({"email": email})
        if result.deleted_count > 0:
            logger.info("user_deleted", email=email)
            return True
        return False

    # ----------------------------
    # SESSION OPERATIONS
    # ----------------------------

    async def create_session(self, session_id: str, user_id: str, name: str = "") -> dict:
        session = {
            "_id": session_id,
            "user_id": user_id,
            "name": name,
        }
        await self.sessions.insert_one(session)
        logger.info("session_created", session_id=session_id)
        return session

    async def delete_session(self, session_id: str) -> bool:
        result = await self.sessions.delete_one({"_id": session_id})
        if result.deleted_count > 0:
            logger.info("session_deleted", session_id=session_id)
            return True
        return False

    async def get_session(self, session_id: str) -> Optional[dict]:
        session = await self.sessions.find_one({"_id": session_id})
        return session

    async def get_user_sessions(self, user_id: str) -> List[dict]:
        sessions = []
        async for session in self.sessions.find({"user_id": user_id}):
            sessions.append(session)
        return sessions

    async def update_session_name(self, session_id: str, name: str) -> dict:
        result = await self.sessions.update_one(
            {"_id": session_id},
            {"$set": {"name": name}},
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")

        session = await self.sessions.find_one({"_id": session_id})
        logger.info("session_name_updated", session_id=session_id, name=name)
        return session

    # ----------------------------
    # HEALTH CHECK
    # ----------------------------

    async def health_check(self) -> bool:
        try:
            await self.client.admin.command("ping")
            return True
        except Exception as e:
            logger.error("mongo_health_check_failed", error=str(e))
            return False


# Singleton instance
database_service = DatabaseService()
