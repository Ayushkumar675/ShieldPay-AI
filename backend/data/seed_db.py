import asyncio
import uuid
import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.models.schemas import User, Policy, LiquidityState

async def seed_demo_data():
    print("🧹 Cleaning database...")
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]

    await db["users"].delete_many({})
    await db["policies"].delete_many({})
    await db["claims"].delete_many({})
    await db["disruptions"].delete_many({})
    await db["fraud_alerts"].delete_many({})
    await db["payout_transactions"].delete_many({})
    await db["liquidity_state"].delete_many({})

    print("🌱 Seeding 20 workers...")
    workers = []
    zones = ["Mumbai-North", "Mumbai-South", "Delhi-East", "Bangalore-TechPark"]
    
    # Create 20 deterministic users
    for i in range(1, 21):
        zone = zones[i % len(zones)]
        worker = User(
            id=str(uuid.uuid4()),
            name=f"Worker {i}",
            email=f"worker{i}@shieldpay.ai",
            phone=f"9876543{i:03d}",
            password_hash="hashed_secret",  # Dummy hash
            role="worker",
            warehouse_id=f"WH-{zone}",
            home_location={"lat": 19.0760 + (i*0.01), "lng": 72.8777 + (i*0.01), "city": zone.split("-")[0], "zone": zone},
            avg_daily_income=800.0 + (i * 15.0),  # Deterministic income variation
            avg_daily_parcels=40 + i,
            reliability_score=0.85 + (0.005 * i),  # High trust baseline
            is_active=True
        )
        workers.append(worker)

    await db["users"].insert_many([w.model_dump() for w in workers])

    print("📜 Creating active policies...")
    policies = []
    for worker in workers:
        policy = Policy(
            id=str(uuid.uuid4()),
            worker_id=worker.id,
            coverage_amount=5000.0,
            premium_amount=200.0,
            status="active",
            start_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
            end_date=datetime.datetime.utcnow() + datetime.timedelta(days=335),
            auto_renew=True
        )
        policies.append(policy)
    
    await db["policies"].insert_many([p.model_dump() for p in policies])
    
    print("💰 Initializing Liquidity State...")
    liquidity = LiquidityState(
        total_premiums=sum(p.premium_amount * 4 for p in policies), # 4 weeks collected
        total_payouts=0.0,
        reserve_balance=50000.0 + sum(p.premium_amount * 4 for p in policies),
        active_policies_count=len(policies),
        liquidity_ratio=2.5  # Healthy start
    )
    await db["liquidity_state"].insert_one(liquidity.model_dump())

    print("✅ Database Seeded Successfully!")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_demo_data())
