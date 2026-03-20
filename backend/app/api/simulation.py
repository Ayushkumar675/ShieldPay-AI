"""
ShieldPay AI — Real Simulation Pipeline
"""
from fastapi import APIRouter
from pydantic import BaseModel
import logging
from app.services.claim_engine import ClaimEngineService
from app.models.database import get_db

logger = logging.getLogger("simulation")
router = APIRouter()

class SimulationRequest(BaseModel):
    city: str = "Mumbai"
    type: str = "weather"
    severity: float = 0.85

@router.post("/simulate-disruption")
async def simulate_disruption(req: SimulationRequest):
    """Phase 5: Simulates a natural or city-wide disruption."""
    logger.info(f"Simulating disruption: {req.type} in {req.city} with severity {req.severity}")
    
    event = {
        "disruption_type": req.type,
        "city": req.city,
        "severity": req.severity
    }
    
    # Phase 8: Return structured debug response
    result = await ClaimEngineService.process_disruption_event(event) # type: ignore
    
    return {
        "status": "success",
        "stats": result.get("stats"),
        "debug": result
    }

@router.post("/simulate-fraud-cluster")
async def simulate_fraud_cluster(city: str = "Delhi"):
    """Phase 5: Simulates an organized GPS spoofing / fraud ring."""
    logger.info(f"Simulating fraud cluster in {city}")
    db = get_db()
    if db is None:
        return {"status": "error", "message": "DB not ready"}
    
    workers = await db["users"].find().to_list(length=10)
    fraud_workers = workers[:min(3, len(workers))]
    
    alerts = []
    for w in fraud_workers:
        alert = {
            "worker_id": w.get("id", ""),
            "alert_type": "ring_detected",
            "severity": 0.95,
            "details": {"ring_id": "simulated_ring"}
        }
        await db["fraud_alerts"].insert_one(alert)
        alerts.append(alert)
        
    # await db["platform_metrics"].update_one({}, {"$inc": {"fraud_alert_count": len(alerts)}}, upsert=True)
    
    logger.warning(f"Generated {len(alerts)} fraud alerts for simulation.")
    return {
        "status": "success",
        "debug": {
            "fraud_alerts_generated": len(alerts),
            "target_city": city
        }
    }

@router.post("/simulate-demand-crash")
async def simulate_demand_crash(city: str = "Mumbai"):
    """Phase 5: Simulates an arbitrary crash in parcel demand triggering risk engine changes."""
    logger.info(f"Simulating demand crash in {city}")
    
    event = {
        "disruption_type": "parcel_allocation_drop",
        "city": city,
        "severity": 0.9
    }
    
    result = await ClaimEngineService.process_disruption_event(event) # type: ignore

    return {
        "status": "success",
        "debug": result
    }
