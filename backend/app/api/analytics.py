"""
ShieldPay AI — Analytics API
"""
from fastapi import APIRouter, Depends
from app.services.analytics_service import AnalyticsService
from app.models.database import get_db

router = APIRouter()

@router.get("/admin-dashboard")
async def get_admin_dashboard():
    """Phase 3: Real aggregated admin metrics."""
    data = await AnalyticsService.get_admin_dashboard()
    return data

@router.get("/worker-dashboard/{worker_id}")
async def get_worker_dashboard(worker_id: str):
    """Real worker metrics."""
    data = await AnalyticsService.get_worker_dashboard(worker_id)
    return data

@router.get("/disruptions")
async def get_disruptions():
    """Active Disruptions from DB."""
    db = get_db()
    disruptions = await db["disruptions"].find().sort("created_at", -1).limit(20).to_list(length=20)
    for d in disruptions:
        d["id"] = str(d.get("id"))
        d["_id"] = str(d.get("_id"))
    return disruptions

@router.get("/claims")
async def get_claims():
    """Recent claims from DB."""
    db = get_db()
    claims = await db["claims"].find().sort("created_at", -1).limit(50).to_list(length=50)
    for c in claims:
        c["id"] = str(c.get("id"))
        c["_id"] = str(c.get("_id"))
    return claims

@router.get("/warehouse-risk")
async def get_warehouse_risk():
    """Real warehouse risk aggregation."""
    db = get_db()
    pipeline = [
        {"$group": {
            "_id": "$warehouse_id",
            "worker_count": {"$sum": 1},
            "avg_reliability": {"$avg": "$reliability_score"}
        }},
        {"$project": {
            "warehouse_id": "$_id",
            "worker_count": 1,
            "avg_reliability": 1,
            "_id": 0
        }}
    ]
    cursor = db["users"].aggregate(pipeline)
    warehouses = await cursor.to_list(length=20)
    
    # Format for frontend
    result = []
    for w in warehouses:
        risk = 1.0 - (w.get("avg_reliability", 1.0) or 1.0)
        result.append({
            "id": w.get("warehouse_id", "Unknown"),
            "riskScore": round(risk * 100, 1),
            "workerCount": w.get("worker_count", 0),
            "location": w.get("warehouse_id", "Unknown").replace("WH-", "")
        })
    return {"warehouses": result}

@router.get("/financial-trend")
async def get_financial_trend():
    return await AnalyticsService.get_financial_trend()

@router.get("/fraud-heatmap")
async def get_fraud_heatmap():
    return await AnalyticsService.get_fraud_heatmap()

@router.get("/fraud-alerts-ai")
async def get_fraud_alerts_ai():
    return await AnalyticsService.get_fraud_alerts()

@router.get("/fraud-rings")
async def get_fraud_rings():
    return await AnalyticsService.get_fraud_rings()

@router.get("/worker-forecast/{worker_id}")
async def get_worker_forecast(worker_id: str):
    return await AnalyticsService.get_worker_forecast(worker_id)
