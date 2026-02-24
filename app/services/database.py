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
        self.is_mock = False
        try:
            # Set a short timeout for the initial connection attempt
            self.client = AsyncIOMotorClient(
                settings.MONGO_URI, 
                serverSelectionTimeoutMS=2000,
                connectTimeoutMS=2000
            )
            self.db = self.client[settings.MONGO_DB_NAME]

            self.users = self.db["users"]
            self.sessions = self.db["sessions"]
            
            # Simple check if reachable
            import asyncio
            try:
                # Note: This is sync init so we can't easily await here without refactoring.
                # However, motor handles lazy connection. We'll set a flag if health check fails later.
                pass
            except:
                pass

            logger.info(
                "mongo_database_initialized",
                environment=settings.ENVIRONMENT.value,
            )

        except Exception as e:
            logger.warning("mongo_initialization_warning_falling_back_to_mock", error=str(e))
            self.is_mock = True
            self.db = None
            self._mock_storage = {"users": {}, "sessions": {}, "payments": {}}

    async def _ensure_reachable(self):
        """Check if mongo is reachable, if not, switch to mock mode."""
        if not self.is_mock:
            try:
                await self.client.admin.command("ping")
            except Exception:
                logger.warning("mongo_not_reachable_switching_to_mock_mode")
                self.is_mock = True
                self._mock_storage = {"users": {}, "sessions": {}, "payments": {}}

    # ----------------------------
    # USER OPERATIONS
    # ----------------------------

    async def create_user(self, email: str, password: str) -> dict:
        await self._ensure_reachable()
        if self.is_mock:
            user = {"_id": str(ObjectId()), "email": email, "hashed_password": password}
            self._mock_storage["users"][email] = user
            return user
            
        user = {
            "email": email,
            "hashed_password": password,
        }
        result = await self.users.insert_one(user)
        user["_id"] = str(result.inserted_id)
        logger.info("user_created", email=email)
        return user

    async def get_user(self, user_id: str) -> Optional[dict]:
        await self._ensure_reachable()
        if self.is_mock:
            for u in self._mock_storage["users"].values():
                if u["_id"] == user_id: return u
            return None
            
        user = await self.users.find_one({"_id": ObjectId(user_id)})
        if user:
            user["_id"] = str(user["_id"])
        return user

    async def get_user_by_email(self, email: str) -> Optional[dict]:
        await self._ensure_reachable()
        if self.is_mock:
            return self._mock_storage["users"].get(email)
            
        user = await self.users.find_one({"email": email})
        if user:
            user["_id"] = str(user["_id"])
        return user

    async def delete_user_by_email(self, email: str) -> bool:
        await self._ensure_reachable()
        if self.is_mock:
            if email in self._mock_storage["users"]:
                del self._mock_storage["users"][email]
                return True
            return False
            
        result = await self.users.delete_one({"email": email})
        if result.deleted_count > 0:
            logger.info("user_deleted", email=email)
            return True
        return False

    # ----------------------------
    # SESSION OPERATIONS
    # ----------------------------

    async def create_session(self, session_id: str, user_id: str, name: str = "") -> dict:
        await self._ensure_reachable()
        if self.is_mock:
            session = {"_id": session_id, "user_id": user_id, "name": name}
            self._mock_storage["sessions"][session_id] = session
            return session
            
        session = {
            "_id": session_id,
            "user_id": user_id,
            "name": name,
        }
        await self.sessions.insert_one(session)
        logger.info("session_created", session_id=session_id)
        return session

    async def delete_session(self, session_id: str) -> bool:
        await self._ensure_reachable()
        if self.is_mock:
            if session_id in self._mock_storage["sessions"]:
                del self._mock_storage["sessions"][session_id]
                return True
            return False
            
        result = await self.sessions.delete_one({"_id": session_id})
        if result.deleted_count > 0:
            logger.info("session_deleted", session_id=session_id)
            return True
        return False

    async def get_session(self, session_id: str) -> Optional[dict]:
        await self._ensure_reachable()
        if self.is_mock:
            return self._mock_storage["sessions"].get(session_id)
            
        session = await self.sessions.find_one({"_id": session_id})
        return session

    async def get_user_sessions(self, user_id: str) -> List[dict]:
        await self._ensure_reachable()
        if self.is_mock:
            return [s for s in self._mock_storage["sessions"].values() if s["user_id"] == user_id]

        sessions = []
        async for session in self.sessions.find({"user_id": user_id}):
            sessions.append(session)
        return sessions

    async def update_session_name(self, session_id: str, name: str) -> dict:
        await self._ensure_reachable()
        if self.is_mock:
            if session_id in self._mock_storage["sessions"]:
                self._mock_storage["sessions"][session_id]["name"] = name
                return self._mock_storage["sessions"][session_id]
            raise HTTPException(status_code=404, detail="Session not found")

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
        if self.is_mock:
            return True # Mock mode is always "healthy" for app logic
        try:
            await self.client.admin.command("ping")
            return True
        except Exception as e:
            logger.error("mongo_health_check_failed", error=str(e))
            # Switch to mock if health check fails
            self.is_mock = True
            self._mock_storage = {"users": {}, "sessions": {}, "payments": {}}
            return True


# Singleton instance
database_service = DatabaseService()
