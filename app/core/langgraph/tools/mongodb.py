"""Tool for interacting with MongoDB via decoupled services."""

from langchain_core.tools import tool

from app.core.logging import logger
from app.services.database import database_service
from app.services.payment import payment_service

@tool
async def user_payment_tool(query_type: str, user_id: str = None, transaction_id: str = None) -> str:
    """Fetch user or payment data from the database.

    Use this tool when you need to:
    - Check payment status (Keywords: payment, transaction, fee, invoice, status)
    - Get user details
    - Verify transaction history
    
    Args:
        query_type: The type of query. Allowed values: 'get_user', 'check_payment', 'get_payment_history'.
        user_id: The ID of the user (required for 'get_user' and 'get_payment_history').
        transaction_id: The ID of the transaction (required for 'check_payment').
    """
    logger.info("user_payment_tool_called", query_type=query_type, user_id=user_id, transaction_id=transaction_id)
    
    try:
        if query_type == "get_user":
            if not user_id:
                return "Error: user_id is required for get_user query."
            
            user = await database_service.get_user_by_email(user_id) # Treating user_id as email for this template
            
            if user:
                return f"User Details: {user}"
            else:
                return f"User with ID/Email {user_id} not found."

        elif query_type == "check_payment":
            if not transaction_id:
                return "Error: transaction_id is required for check_payment."
            
            payment = await payment_service.get_payment_by_id(transaction_id)
            
            if payment:
                return f"Payment Details: {payment}"
            else:
                return f"Payment with ID {transaction_id} not found."
                
        elif query_type == "get_payment_history":
             if not user_id:
                return "Error: user_id is required for get_payment_history query."
             
             payments = await payment_service.get_user_payment_history(user_id)
             
             if payments:
                 return f"Recent Payments for {user_id}: {payments}"
             else:
                 return f"No payment history found for user {user_id}."

        else:
            return f"Error: Unknown query_type '{query_type}'."

    except Exception as e:
        logger.error("mongodb_tool_error", error=str(e))
        return f"Error executing database query: {str(e)}"
