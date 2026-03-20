"""
ShieldPay AI — Fraud Analytics API
Trust score queries, fraud dashboard data, admin analytics.
"""
from fastapi import APIRouter, Depends
from typing import Optional

from app.models.database import get_db
from app.core.auth import get_current_user, require_admin

router = APIRouter()


@router.get("/trust-score/{worker_id}")
async def get_trust_score(worker_id: str, current_user: dict = Depends(get_current_user)):
    """Get trust score for a specific worker."""
    from app.ai.trust_scorer import compute_trust_score
    trust = await compute_trust_score(worker_id)
    return {"trust_score": trust.model_dump()}


@router.get("/alerts")
async def get_fraud_alerts(
    severity_min: float = 0.0,
    limit: int = 50,
    current_user: dict = Depends(require_admin)
):
    """Admin: Get recent fraud alerts."""
    db = get_db()
    cursor = db.fraud_alerts.find(
        {"severity": {"$gte": severity_min}},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit)
    alerts = await cursor.to_list(length=limit)
    return {"alerts": alerts, "total": len(alerts)}


@router.get("/rings")
async def get_fraud_rings(current_user: dict = Depends(require_admin)):
    """Admin: Get detected fraud rings."""
    db = get_db()
    cursor = db.fraud_rings.find({}, {"_id": 0}).sort("created_at", -1)
    rings = await cursor.to_list(length=20)
    return {"fraud_rings": rings}


@router.get("/heatmap")
async def get_fraud_heatmap(current_user: dict = Depends(require_admin)):
    """Admin: Get fraud heatmap data — geographic distribution of fraud alerts."""
    db = get_db()

    # Aggregate fraud alerts by zone
    pipeline = [
        {"$lookup": {
            "from": "users",
            "localField": "worker_id",
            "foreignField": "id",
            "as": "worker_info"
        }},
        {"$unwind": {"path": "$worker_info", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": "$worker_info.warehouse_id",
            "alert_count": {"$sum": 1},
            "avg_severity": {"$avg": "$severity"},
            "worker_ids": {"$addToSet": "$worker_id"},
        }},
        {"$sort": {"alert_count": -1}},
    ]
    results = await db.fraud_alerts.aggregate(pipeline).to_list(length=100)

    # Enrich with warehouse location data
    heatmap_data = []
    for r in results:
        wh_id = r["_id"]
        if wh_id:
            # Try to get warehouse coordinates from workers' data
            worker = await db.users.find_one({"warehouse_id": wh_id, "home_location": {"$exists": True}})
            loc = worker.get("home_location", {}) if worker else {}
            heatmap_data.append({
                "warehouse_id": wh_id,
                "lat": loc.get("lat", 0),
                "lng": loc.get("lng", 0),
                "alert_count": r["alert_count"],
                "avg_severity": round(r["avg_severity"], 3),
                "unique_workers": len(r["worker_ids"]),
            })

    return {"heatmap": heatmap_data}


@router.get("/analytics")
async def get_fraud_analytics(current_user: dict = Depends(require_admin)):
    """Admin: Get overall fraud analytics dashboard data."""
    db = get_db()

    total_claims = await db.claims.count_documents({})
    auto_approved = await db.claims.count_documents({"status": "auto_approved"})
    soft_verify = await db.claims.count_documents({"status": "soft_verify"})
    delayed = await db.claims.count_documents({"status": "delayed_review"})
    rejected = await db.claims.count_documents({"status": "rejected"})
    total_alerts = await db.fraud_alerts.count_documents({})
    total_rings = await db.fraud_rings.count_documents({})

    # Premium vs payout
    premium_pipeline = [
        {"$match": {"type": "premium_collected"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    payout_pipeline = [
        {"$match": {"type": "claim_payout"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]

    premium_result = await db.payments.aggregate(premium_pipeline).to_list(1)
    payout_result = await db.payments.aggregate(payout_pipeline).to_list(1)

    total_premiums = premium_result[0]["total"] if premium_result else 0
    total_payouts = payout_result[0]["total"] if payout_result else 0

    return {
        "claims_breakdown": {
            "total": total_claims,
            "auto_approved": auto_approved,
            "soft_verify": soft_verify,
            "delayed_review": delayed,
            "rejected": rejected,
        },
        "fraud_stats": {
            "total_alerts": total_alerts,
            "total_rings": total_rings,
        },
        "financials": {
            "total_premiums_collected": total_premiums,
            "total_payouts": total_payouts,
            "liquidity_ratio": round(total_premiums / max(total_payouts, 1), 3),
        }
    }
