"""
ShieldPay AI — MongoDB Database Connection & Helpers
Async MongoDB access via motor driver.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client: AsyncIOMotorClient = None
db = None


async def connect_db():
    """Initialize MongoDB connection on app startup."""
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    # Create indexes for common queries
    await db["users"].create_index("email", unique=True)
    await db["users"].create_index("phone")
    await db["users"].create_index("warehouse_id")
    await db["policies"].create_index("worker_id")
    await db["claims"].create_index("worker_id")
    await db["claims"].create_index("trigger_id")
    await db["claims"].create_index("status")
    await db['disruption_triggers'].create_index("affected_zone")
    await db['disruption_triggers'].create_index("is_active")
    await db["fraud_alerts"].create_index("worker_id")
    await db["payout_transactions"].create_index("worker_id")
    await db["payout_transactions"].create_index("claim_id")
    await db["liquidity_state"].create_index("last_updated")
    print(f"✅ Connected to MongoDB: {settings.MONGODB_DB_NAME}")


async def close_db():
    """Close MongoDB connection on app shutdown."""
    global client
    if client:
        client.close()
        print("🔌 MongoDB connection closed")


def get_db():
    """Get database instance."""
    return db
