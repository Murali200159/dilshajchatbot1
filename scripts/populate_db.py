
import asyncio
import sys
import os
from datetime import datetime

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.services.database import database_service
from app.services.payment import payment_service

async def populate_db():
    print("Populating MongoDB with sample data...")
    
    # 1. Create a sample user
    email = "sarip@dilshajinfotech.com"
    password = "securepassword123"
    
    # Check if user exists
    existing_user = await database_service.get_user_by_email(email)
    if existing_user:
        print(f"User {email} already exists.")
        user_id = existing_user["email"]
    else:
        print(f"Creating user {email}...")
        user = await database_service.create_user(email, password)
        user_id = user["email"]
        print(f"User created: {user}")

    # 2. Create sample payments
    payments_collection = database_service.db["payments"]
    
    sample_payments = [
        {
            "user_id": user_id,
            "transaction_id": "TXN_1001",
            "amount": 5000,
            "currency": "INR",
            "status": "COMPLETED",
            "description": "Course Fee - Installment 1",
            "date": datetime.now().isoformat()
        },
        {
            "user_id": user_id,
            "transaction_id": "TXN_1002",
            "amount": 1500,
            "currency": "INR",
            "status": "PENDING",
            "description": "Exam Fee",
            "date": datetime.now().isoformat()
        }
    ]
    
    for payment in sample_payments:
        # Check if payment exists
        existing_payment = await payments_collection.find_one({"transaction_id": payment["transaction_id"]})
        if existing_payment:
             print(f"Payment {payment['transaction_id']} already exists.")
        else:
            await payments_collection.insert_one(payment)
            print(f"Payment {payment['transaction_id']} created.")

    print("Database population complete.")

if __name__ == "__main__":
    asyncio.run(populate_db())
