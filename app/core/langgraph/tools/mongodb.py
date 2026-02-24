"""Tool for querying user payment data from MongoDB."""

from langchain_core.tools import tool

from app.core.logging import logger
from app.services.payment import payment_service


@tool
async def user_payment_tool(query_type: str, user_id: str = None, transaction_id: str = None) -> str:
    """Fetch user payment data from the MongoDB database.

    Use this tool when the user asks about:
    - Their payment status, transaction, invoice, fee
    - "Did I pay?", "show my payments", "what is my transaction status?"
    - A specific transaction ID like TXN001, TXN002 etc.
    - Payment history for a user

    Args:
        query_type: One of:
            'check_payment'       → look up a specific transaction by transaction_id
            'get_payment_history' → get all payments for a user_id or email
            'get_all_payments'    → list recent payments (no user_id needed)
        user_id: The user's ID, email, or name (for history queries).
        transaction_id: The transaction ID like TXN001 (for check_payment).
    """
    logger.info("user_payment_tool_called",
                query_type=query_type, user_id=user_id, transaction_id=transaction_id)

    # Ensure sample data exists for demo/testing
    await payment_service.seed_sample_data()

    try:
        # ── Check a specific transaction ──────────────────────────────────────
        if query_type == "check_payment":
            if not transaction_id:
                return "Please provide a transaction ID (e.g. TXN001) to check payment status."

            payment = await payment_service.get_payment_by_id(transaction_id.strip().upper())
            if payment:
                return (
                    f"✅ Payment Found:\n"
                    f"  • Transaction ID : {payment.get('transaction_id')}\n"
                    f"  • Name           : {payment.get('name', 'N/A')}\n"
                    f"  • Service        : {payment.get('service', 'N/A')}\n"
                    f"  • Amount         : ₹{payment.get('amount')} {payment.get('currency','INR')}\n"
                    f"  • Status         : {payment.get('status', 'N/A').upper()}\n"
                    f"  • Date           : {payment.get('date', 'N/A')}"
                )
            return f"❌ No payment found with transaction ID: {transaction_id}"

        # ── Get payment history for a specific user ───────────────────────────
        elif query_type == "get_payment_history":
            if not user_id:
                return "Please provide a user ID or email to fetch payment history."

            payments = await payment_service.get_user_payment_history(user_id.strip())
            if payments:
                lines = [f"📋 Payment History for '{user_id}':"]
                for p in payments:
                    lines.append(
                        f"  • {p.get('transaction_id')} | {p.get('service','N/A')} "
                        f"| ₹{p.get('amount')} | {p.get('status','').upper()} | {p.get('date','')}"
                    )
                return "\n".join(lines)
            return f"No payment history found for user: {user_id}"

        # ── List all recent payments ──────────────────────────────────────────
        elif query_type == "get_all_payments":
            payments = await payment_service.get_all_payments(limit=10)
            if payments:
                lines = ["📋 Recent Payments:"]
                for p in payments:
                    lines.append(
                        f"  • {p.get('transaction_id')} | {p.get('name','N/A')} "
                        f"| {p.get('service','N/A')} | ₹{p.get('amount')} "
                        f"| {p.get('status','').upper()} | {p.get('date','')}"
                    )
                return "\n".join(lines)
            return "No payment records found in the database."

        else:
            return (
                f"Unknown query_type '{query_type}'. "
                "Use: 'check_payment', 'get_payment_history', or 'get_all_payments'."
            )

    except Exception as e:
        logger.error("mongodb_tool_error", error=str(e))
        return f"Error querying payment database: {str(e)}"
