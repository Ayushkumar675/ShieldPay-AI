import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(r"c:\ShieldPay AI\backend").resolve()))

from app.services.claim_engine import ClaimEngineService
from app.models.database import connect_db, close_db, get_db

async def main():
    print("Connecting to DB...")
    await connect_db()
    
    db = get_db()
    # Ensure there's a test user and policy
    test_worker_id = "test-worker-alpha"
    await db.users.update_one(
        {"id": test_worker_id},
        {"$set": {
            "name": "Test Alpha",
            "home_location": {"city": "Mumbai"},
            "avg_daily_parcels": 40
        }},
        upsert=True
    )
    
    await db.policies.update_one(
        {"worker_id": test_worker_id},
        {"$set": {
            "id": "test-policy-123",
            "status": "active",
            "coverage_amount": 2500,
            "premium_amount": 50
        }},
        upsert=True
    )
    
    print("Testing disruption event processing...")
    event = {
        "disruption_type": "weather",
        "city": "Mumbai",
        "severity": 0.85
    }
    
    result = await ClaimEngineService.process_disruption_event(event)
    print("Result:", result)
    
    await close_db()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
