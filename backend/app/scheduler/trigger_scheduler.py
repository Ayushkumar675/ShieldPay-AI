"""
ShieldPay AI — Parametric Trigger Scheduler
Scans for disruption triggers every 20 minutes,
evaluates affected workers, and auto-creates claims.
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict

from app.core.config import settings


class TriggerScheduler:
    """
    Event-driven scheduler that runs every 20 minutes to:
    1. Scan external data sources for disruption signals
    2. Detect parametric trigger conditions
    3. Auto-create claims for affected insured workers
    4. Cross-reference with fraud layer before payout
    """

    def __init__(self):
        self.is_running = False
        self.scan_count = 0
        self.last_scan = None

    async def start(self):
        """Start the periodic scan loop."""
        self.is_running = True
        print(f"⚡ Trigger Scheduler started (interval: {settings.TRIGGER_SCAN_INTERVAL_MINUTES}min)")
        while self.is_running:
            try:
                await self.scan_for_triggers()
            except Exception as e:
                print(f"❌ Scheduler error: {e}")
            await asyncio.sleep(settings.TRIGGER_SCAN_INTERVAL_MINUTES * 60)

    async def stop(self):
        """Stop the scheduler."""
        self.is_running = False
        print("🛑 Trigger Scheduler stopped")

    async def scan_for_triggers(self):
        """Execute a full disruption scan cycle."""
        self.scan_count += 1
        self.last_scan = datetime.utcnow()
        print(f"\n🔍 Scan #{self.scan_count} at {self.last_scan.isoformat()}")

        from app.models.database import get_db
        db = get_db()
        if not db:
            print("  ⚠ Database not connected, skipping scan")
            return

        # Step 1: Check weather conditions
        weather_triggers = await self._check_weather_triggers(db)

        # Step 2: Check warehouse status
        warehouse_triggers = await self._check_warehouse_triggers(db)

        # Step 3: Check traffic conditions
        traffic_triggers = await self._check_traffic_triggers(db)

        all_triggers = weather_triggers + warehouse_triggers + traffic_triggers
        print(f"  📡 Detected {len(all_triggers)} new triggers")

        # Step 4: For each trigger, find affected insured workers
        for trigger in all_triggers:
            await self._process_trigger(db, trigger)

        # Step 5: Check and resolve expired triggers
        await self._resolve_expired_triggers(db)

    async def _check_weather_triggers(self, db) -> List[Dict]:
        """Check weather APIs for disruption-level conditions."""
        from app.api.integrations import MOCK_WEATHER_CONDITIONS
        from app.models.schemas import DisruptionTrigger, DisruptionType

        triggers = []
        for city, weather in MOCK_WEATHER_CONDITIONS.items():
            if weather["severity"] >= 0.6:  # Threshold for trigger
                # Check if trigger already exists for this city
                existing = await db.disruption_triggers.find_one({
                    "type": "weather",
                    "location.city": city,
                    "is_active": True
                })
                if not existing:
                    trigger = DisruptionTrigger(
                        type=DisruptionType.WEATHER,
                        severity=weather["severity"],
                        affected_zone=f"ZONE-{city[:3].upper()}-1",
                        location={"lat": 0, "lng": 0, "city": city},
                        description=f"Severe {weather['condition'].replace('_', ' ')} in {city}",
                        weather_data=weather,
                        is_active=True,
                    )
                    await db.disruption_triggers.insert_one(trigger.model_dump())
                    triggers.append(trigger.model_dump())
                    print(f"  🌧  Weather trigger: {city} (severity: {weather['severity']})")

        return triggers

    async def _check_warehouse_triggers(self, db) -> List[Dict]:
        """Check warehouse operational status."""
        import random
        from app.models.schemas import DisruptionTrigger, DisruptionType

        triggers = []
        # Get all unique warehouse IDs
        warehouse_ids = await db.users.distinct("warehouse_id")

        for wh_id in warehouse_ids[:5]:  # Check top 5 warehouses
            if not wh_id:
                continue
            # Simulate warehouse check (20% chance of disruption)
            if random.random() < 0.15:
                existing = await db.disruption_triggers.find_one({
                    "type": "warehouse_shutdown",
                    "affected_warehouse_ids": wh_id,
                    "is_active": True,
                })
                if not existing:
                    trigger = DisruptionTrigger(
                        type=DisruptionType.WAREHOUSE_SHUTDOWN,
                        severity=round(random.uniform(0.5, 0.9), 2),
                        affected_zone=f"ZONE-WH-{wh_id}",
                        affected_warehouse_ids=[wh_id],
                        location={"lat": 0, "lng": 0, "city": ""},
                        description=f"Warehouse {wh_id} operations disrupted",
                        is_active=True,
                    )
                    await db.disruption_triggers.insert_one(trigger.model_dump())
                    triggers.append(trigger.model_dump())
                    print(f"  🏭 Warehouse trigger: {wh_id}")

        return triggers

    async def _check_traffic_triggers(self, db) -> List[Dict]:
        """Check traffic conditions for gridlock triggers."""
        import random
        from app.models.schemas import DisruptionTrigger, DisruptionType

        triggers = []
        cities = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata"]

        for city in cities:
            congestion = random.uniform(0.4, 1.0)
            if congestion > 0.85:  # Severe gridlock
                existing = await db.disruption_triggers.find_one({
                    "type": "traffic_gridlock",
                    "location.city": city,
                    "is_active": True,
                })
                if not existing:
                    trigger = DisruptionTrigger(
                        type=DisruptionType.TRAFFIC_GRIDLOCK,
                        severity=round(congestion, 2),
                        affected_zone=f"ZONE-{city[:3].upper()}-1",
                        location={"lat": 0, "lng": 0, "city": city},
                        description=f"Severe traffic gridlock in {city}",
                        traffic_data={"congestion_index": congestion},
                        is_active=True,
                    )
                    await db.disruption_triggers.insert_one(trigger.model_dump())
                    triggers.append(trigger.model_dump())
                    print(f"  🚗 Traffic trigger: {city} (congestion: {congestion:.2f})")

        return triggers

    async def _process_trigger(self, db, trigger: Dict):
        """Find affected insured workers and auto-create claims."""
        from app.services.claim_automation import auto_create_claim

        # Find workers in affected zone/warehouse
        query = {"role": "worker", "is_active": True}
        if trigger.get("affected_warehouse_ids"):
            query["warehouse_id"] = {"$in": trigger["affected_warehouse_ids"]}

        workers = await db.users.find(query).to_list(length=100)
        print(f"  👷 {len(workers)} workers in affected zone")

        claims_created = 0
        for worker in workers:
            # Check if worker has active policy
            policy = await db.policies.find_one({
                "worker_id": worker["id"],
                "status": "active"
            })
            if policy:
                # Check for existing claim for this trigger
                existing = await db.claims.find_one({
                    "worker_id": worker["id"],
                    "trigger_id": trigger["id"]
                })
                if not existing:
                    await auto_create_claim(worker["id"], policy["id"], trigger)
                    claims_created += 1

        print(f"  📝 Auto-created {claims_created} claims")

    async def _resolve_expired_triggers(self, db):
        """Resolve triggers that have been active for > 72 hours."""
        cutoff = datetime.utcnow() - timedelta(hours=72)
        result = await db.disruption_triggers.update_many(
            {"is_active": True, "detected_at": {"$lt": cutoff}},
            {"$set": {"is_active": False, "resolved_at": datetime.utcnow()}}
        )
        if result.modified_count:
            print(f"  ✅ Resolved {result.modified_count} expired triggers")

    def get_status(self) -> Dict:
        return {
            "is_running": self.is_running,
            "scan_count": self.scan_count,
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
            "interval_minutes": settings.TRIGGER_SCAN_INTERVAL_MINUTES,
        }


# Singleton instance
scheduler = TriggerScheduler()
