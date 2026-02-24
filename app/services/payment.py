"""Payment service for handling transaction and payment operations in MongoDB."""

from typing import List, Optional
from app.core.logging import logger
from app.services.database import database_service


class PaymentService:
    """Service for handling payment and transaction operations."""

    @property
    def collection(self):
        """Lazy collection access so mock mode works correctly."""
        if database_service.is_mock:
            return None
        return database_service.db["payments"]

    # ------------------------------------------------------------------
    # PAYMENT BY TRANSACTION ID
    # ------------------------------------------------------------------
    async def get_payment_by_id(self, transaction_id: str) -> Optional[dict]:
        """Fetch a specific payment by transaction_id."""
        await database_service._ensure_reachable()
        try:
            if database_service.is_mock:
                for p in database_service._mock_storage.get("payments", {}).values():
                    if p.get("transaction_id") == transaction_id:
                        return p
                return None

            payment = await self.collection.find_one({"transaction_id": transaction_id})
            if payment:
                payment.pop("_id", None)
            return payment
        except Exception as e:
            logger.error("payment_fetch_failed", transaction_id=transaction_id, error=str(e))
            return None

    # ------------------------------------------------------------------
    # PAYMENT HISTORY FOR USER
    # ------------------------------------------------------------------
    async def get_user_payment_history(self, user_id: str, limit: int = 5) -> List[dict]:
        """Fetch recent payment history for a user (by user_id or email)."""
        await database_service._ensure_reachable()
        try:
            if database_service.is_mock:
                all_payments = list(database_service._mock_storage.get("payments", {}).values())
                return [
                    p for p in all_payments
                    if p.get("user_id") == user_id or p.get("email") == user_id
                ][:limit]

            # Search by user_id OR email
            cursor = self.collection.find(
                {"$or": [{"user_id": user_id}, {"email": user_id}]}
            ).sort("date", -1).limit(limit)
            payments = await cursor.to_list(length=limit)
            for p in payments:
                p.pop("_id", None)
            return payments
        except Exception as e:
            logger.error("payment_history_fetch_failed", user_id=user_id, error=str(e))
            return []

    # ------------------------------------------------------------------
    # ALL PAYMENTS (for admin / summary)
    # ------------------------------------------------------------------
    async def get_all_payments(self, limit: int = 10) -> List[dict]:
        """Fetch recent payments across all users."""
        await database_service._ensure_reachable()
        try:
            if database_service.is_mock:
                return list(database_service._mock_storage.get("payments", {}).values())[:limit]

            cursor = self.collection.find().sort("date", -1).limit(limit)
            payments = await cursor.to_list(length=limit)
            for p in payments:
                p.pop("_id", None)
            return payments
        except Exception as e:
            logger.error("all_payments_fetch_failed", error=str(e))
            return []

    # ------------------------------------------------------------------
    # SEED SAMPLE DATA (for testing when DB is empty)
    # ------------------------------------------------------------------
    async def seed_sample_data(self):
        """Insert sample payment data if collection is empty."""
        await database_service._ensure_reachable()
        try:
            if database_service.is_mock:
                if not database_service._mock_storage.get("payments"):
                    database_service._mock_storage["payments"] = {
                        "TXN001": {
                            "transaction_id": "TXN001",
                            "user_id": "user_001",
                            "email": "john@example.com",
                            "name": "John Doe",
                            "amount": 2999,
                            "currency": "INR",
                            "status": "success",
                            "service": "Web Development Course",
                            "date": "2024-01-15",
                        },
                        "TXN002": {
                            "transaction_id": "TXN002",
                            "user_id": "user_002",
                            "email": "priya@example.com",
                            "name": "Priya Sharma",
                            "amount": 4999,
                            "currency": "INR",
                            "status": "success",
                            "service": "Full Stack Training",
                            "date": "2024-02-10",
                        },
                        "TXN003": {
                            "transaction_id": "TXN003",
                            "user_id": "user_003",
                            "email": "ravi@example.com",
                            "name": "Ravi Kumar",
                            "amount": 1500,
                            "currency": "INR",
                            "status": "pending",
                            "service": "UI/UX Design",
                            "date": "2024-03-05",
                        },
                    }
                logger.info("sample_payments_seeded_mock")
                return

            count = await self.collection.count_documents({})
            if count == 0:
                sample = [
                    {
                        "transaction_id": "TXN001",
                        "user_id": "user_001",
                        "email": "john@example.com",
                        "name": "John Doe",
                        "amount": 2999,
                        "currency": "INR",
                        "status": "success",
                        "service": "Web Development Course",
                        "date": "2024-01-15",
                    },
                    {
                        "transaction_id": "TXN002",
                        "user_id": "user_002",
                        "email": "priya@example.com",
                        "name": "Priya Sharma",
                        "amount": 4999,
                        "currency": "INR",
                        "status": "success",
                        "service": "Full Stack Training",
                        "date": "2024-02-10",
                    },
                    {
                        "transaction_id": "TXN003",
                        "user_id": "user_003",
                        "email": "ravi@example.com",
                        "name": "Ravi Kumar",
                        "amount": 1500,
                        "currency": "INR",
                        "status": "pending",
                        "service": "UI/UX Design",
                        "date": "2024-03-05",
                    },
                ]
                await self.collection.insert_many(sample)
                logger.info("sample_payments_seeded_mongo", count=len(sample))
        except Exception as e:
            logger.error("seed_sample_data_failed", error=str(e))


# Singleton instance
payment_service = PaymentService()
