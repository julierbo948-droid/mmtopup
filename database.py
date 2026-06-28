from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from config import Config

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client.mlbb_bot
        self.users = self.db.users
        self.transactions = self.db.transactions

    async def get_user(self, user_id: int):
        return await self.users.find_one({"user_id": user_id})

    async def create_user(self, user_id: int, username: str):
        user = {
            "user_id": user_id,
            "username": username,
            "balance": 0,
            "created_at": datetime.utcnow()
        }
        await self.users.insert_one(user)
        return user

    async def update_balance(self, user_id: int, amount: int):
        await self.users.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": amount}}
        )
        user = await self.get_user(user_id)
        return user["balance"]

    async def log_transaction(self, user_id: int, type: str, amount: int, description: str, status: str = "completed"):
        transaction = {
            "user_id": user_id,
            "type": type, # e.g., "deposit", "diamond_purchase"
            "amount": amount,
            "description": description,
            "status": status,
            "timestamp": datetime.utcnow()
        }
        await self.transactions.insert_one(transaction)
        return transaction

    async def get_transactions(self, user_id: int, limit: int = 10):
        return await self.transactions.find({"user_id": user_id}).sort("timestamp", -1).limit(limit).to_list(length=limit)
