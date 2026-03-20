"""
ShieldPay AI — Analytics & Dashboard Service
Aggregates real-time metrics from MongoDB.
"""
from app.models.database import get_db
from app.services.liquidity_engine import LiquidityEngineService

class AnalyticsService:
    @staticmethod
    async def get_admin_dashboard():
        db = get_db()
        if db is None:
            return {}

        liquidity = await LiquidityEngineService.get_state()
        
        workers_count = await db["users"].count_documents({"role": "worker"})
        active_policies = await db["policies"].count_documents({"status": "active"})
        fraud_alerts = await db["fraud_alerts"].count_documents({"resolved": False})
        active_disruptions = await db["disruptions"].count_documents({"is_active": True})
        
        # Recent claims
        recent_claims = await db["claims"].find().sort("created_at", -1).limit(5).to_list(length=5)
        # Serialize ObjectIds
        for c in recent_claims:
            c["id"] = str(c.get("id"))
            c["_id"] = str(c.get("_id"))

        # Claims Breakdown
        pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
        breakdown_cursor = db["claims"].aggregate(pipeline)
        breakdown_list = await breakdown_cursor.to_list(length=10)
        
        claims_breakdown = {
            "total": await db["claims"].count_documents({}),
            "auto_approved": 0,
            "soft_verify": 0,
            "delayed_review": 0,
            "rejected": 0
        }
        for item in breakdown_list:
            status = item["_id"]
            if status == "auto_approved" or status == "paid":
                claims_breakdown["auto_approved"] += item["count"]
            elif status == "soft_verify":
                claims_breakdown["soft_verify"] += item["count"]
            elif status == "delayed_review" or status == "pending":
                claims_breakdown["delayed_review"] += item["count"]
            elif status == "rejected":
                claims_breakdown["rejected"] += item["count"]

        return {
            "liquidity": liquidity,
            "metrics": {
                "total_workers": workers_count,
                "active_policies": active_policies,
                "fraud_alerts_count": fraud_alerts,
                "active_disruptions": active_disruptions
            },
            "recent_claims": recent_claims,
            "claims_breakdown": claims_breakdown
        }

    @staticmethod
    async def get_worker_dashboard(worker_id: str):
        db = get_db()
        if db is None:
            return {}

        user = await db["users"].find_one({"id": worker_id})
        policy = await db["policies"].find_one({"worker_id": worker_id, "status": "active"})
        claims = await db["claims"].find({"worker_id": worker_id}).sort("created_at", -1).limit(10).to_list(length=10)
        trust = await db["trust_scores"].find_one({"worker_id": worker_id}, sort=[("computed_at", -1)])

        # Serialize
        for c in claims:
            c["id"] = str(c.get("id"))
            c["_id"] = str(c.get("_id"))

        return {
            "worker_profile": {
                "name": user.get("name"),
                "avg_income": user.get("avg_daily_income"),
                "reliability": user.get("reliability_score")
            },
            "policy": {
                "coverage": policy.get("coverage_amount") if policy else 0,
                "premium": policy.get("premium_amount") if policy else 0
            },
            "trust_score": trust.get("composite_score", 0.85) if trust else 0.85,
            "claims_history": claims
        }
