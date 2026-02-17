"""Payment service for handling transaction and payment operations in MongoDB."""

from typing import List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.services.database import database_service

class PaymentService:
    """Service for handling payment and transaction operations."""

    def __init__(self):
        self.db = database_service.db
        self.collection = self.db["payments"]

    async def get_payment_by_id(self, transaction_id: str) -> Optional[dict]:
        """Fetch a specific payment by its transaction status."""
        try:
            payment = await self.collection.find_one({"transaction_id": transaction_id})
            if payment and "_id" in payment:
                del payment["_id"]
            return payment
        except Exception as e:
            logger.error("payment_fetch_failed", transaction_id=transaction_id, error=str(e))
            return None

    async def get_user_payment_history(self, user_id: str, limit: int = 5) -> List[dict]:
        """Fetch recent payment history for a specific user."""
        try:
            cursor = self.collection.find({"user_id": user_id}).limit(limit)
            payments = await cursor.to_list(length=limit)
            for p in payments:
                if "_id" in p:
                    del p["_id"]
            return payments
        except Exception as e:
            logger.error("payment_history_fetch_failed", user_id=user_id, error=str(e))
            return []

# Singleton instance
payment_service = PaymentService()
