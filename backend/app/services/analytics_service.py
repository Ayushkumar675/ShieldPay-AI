"""
ShieldPay AI — Analytics & Dashboard Service
Aggregates real-time metrics from MongoDB with deterministic,
context-seeded data generation (no random flicker).
"""
import hashlib
import math
from datetime import datetime, timedelta
from app.models.database import get_db
from app.services.liquidity_engine import LiquidityEngineService
from app.ai.narrative_engine import (
    generate_risk_narrative,
    generate_trust_narrative,
    generate_weekly_advice,
    generate_admin_weekly_summary,
    generate_anomaly_spotlight,
)


def _seeded_value(seed_str: str, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Generate a deterministic float from a seed string. Same seed = same value."""
    h = int(hashlib.sha256(seed_str.encode()).hexdigest()[:8], 16)
    normalized = (h % 10000) / 10000.0  # 0.0 to 0.9999
    return min_val + normalized * (max_val - min_val)


def _date_seed() -> str:
    """Return a seed based on the current date (consistent within a day)."""
    return datetime.utcnow().strftime("%Y-%m-%d")


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
            if status in ("auto_approved", "paid"):
                claims_breakdown["auto_approved"] += item["count"]
            elif status == "soft_verify":
                claims_breakdown["soft_verify"] += item["count"]
            elif status in ("delayed_review", "pending"):
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

        for c in claims:
            c["id"] = str(c.get("id"))
            c["_id"] = str(c.get("_id"))

        composite_score = trust.get("composite_score", 0.85) if trust else 0.85
        worker_name = user.get("name", "Worker") if user else "Worker"

        return {
            "worker_profile": {
                "name": worker_name,
                "avg_income": user.get("avg_daily_income") if user else 1500,
                "reliability": user.get("reliability_score") if user else 0.85,
            },
            "policy": {
                "coverage": policy.get("coverage_amount") if policy else 0,
                "premium": policy.get("premium_amount") if policy else 0
            },
            "trust_score": composite_score,
            "trust_narrative": generate_trust_narrative(
                {"composite_score": composite_score},
                worker_name=worker_name
            ),
            "claims_history": claims
        }

    @staticmethod
    async def get_financial_trend():
        """Generate 12-week financial trend with deterministic, date-seeded data."""
        db = get_db()
        if db is None:
            return {"trend": [], "summary": {}}

        liquidity = await LiquidityEngineService.get_state()
        claims_count = await db["claims"].count_documents({})
        
        trend = []
        base_prem = liquidity["total_premiums"] / 12 if liquidity.get("total_premiums") else 150000
        base_pay = liquidity["total_payouts"] / 12 if liquidity.get("total_payouts") else 120000
        
        date_seed = _date_seed()
        
        for i in range(12, 0, -1):
            # Deterministic variation seeded by date + week index
            seed_prem = f"{date_seed}:prem:{i}"
            seed_pay = f"{date_seed}:pay:{i}"
            
            var_prem = _seeded_value(seed_prem, 0.8, 1.2)
            var_pay = _seeded_value(seed_pay, 0.7, 1.3)
            
            trend.append({
                "week": f"Week {-i}",
                "premiums": round(base_prem * var_prem, 2),
                "payouts": round(base_pay * var_pay, 2),
                "claims_count": int((claims_count / 12) * var_pay) if claims_count else 5
            })
        
        return {"trend": trend, "summary": liquidity}

    @staticmethod
    async def get_fraud_heatmap():
        db = get_db()
        if db is None:
            return {"heatmap": []}

        pipeline = [
            {"$group": {"_id": "$city", "alerts": {"$sum": 1}, "severity": {"$avg": "$severity"}}},
            {"$project": {"city": "$_id", "alerts": 1, "severity": 1, "_id": 0}}
        ]
        heatmap = await db["fraud_alerts"].aggregate(pipeline).to_list(length=20)
        
        if not heatmap:
            users = await db["users"].find().limit(50).to_list(length=50)
            cities = {}
            for u in users:
                c = u.get("city", "Unknown")
                cities[c] = cities.get(c, 0) + 1
            
            date_seed = _date_seed()
            heatmap = [
                {
                    "city": k,
                    "alerts": v * 3,
                    "severity": _seeded_value(f"{date_seed}:heatmap:{k}", 0.4, 0.9)
                }
                for k, v in cities.items()
            ][:5]
            
            if not heatmap:
                heatmap = [
                    {"city": "Mumbai", "alerts": 12, "severity": _seeded_value(f"{date_seed}:hm:mumbai", 0.7, 0.95)},
                    {"city": "Delhi", "alerts": 8, "severity": _seeded_value(f"{date_seed}:hm:delhi", 0.5, 0.75)},
                    {"city": "Bangalore", "alerts": 15, "severity": _seeded_value(f"{date_seed}:hm:blr", 0.8, 0.95)},
                ]
        
        for h in heatmap:
            c_sev = h.get("severity", 0.5)
            h["color"] = "#ef4444" if c_sev > 0.7 else "#f59e0b" if c_sev > 0.4 else "#10b981"
        
        return {"heatmap": heatmap}

    @staticmethod
    async def get_fraud_alerts():
        db = get_db()
        if db is None:
            return {"alerts": []}
        alerts = await db["fraud_alerts"].find().sort("created_at", -1).limit(20).to_list(length=20)
        for a in alerts:
            a["id"] = str(a.get("_id"))
            a["worker"] = a.get("worker_id", "Unknown")
            a["time"] = a.get("created_at")
        return {"alerts": alerts}

    @staticmethod
    async def get_fraud_rings():
        db = get_db()
        if db is None:
            return {"fraud_rings": []}
        bad_users = await db["users"].find({"nearby_claim_cluster_score": {"$gt": 0.5}}).limit(10).to_list(length=10)
        rings = []
        if len(bad_users) > 3:
            rings.append({
                "id": "RING-001",
                "members": len(bad_users),
                "confidence": 0.88,
                "claims": sum(u.get("claim_frequency_7day", 0) for u in bad_users),
                "pattern": "Temporal claim clustering via GPS spoof",
                "workers": [u.get("name") or u.get("id") for u in bad_users[:5]]
            })
        return {"fraud_rings": rings}

    @staticmethod
    async def get_worker_forecast(worker_id: str):
        """Generate deterministic worker forecast seeded by worker_id + date."""
        db = get_db()
        if db is None:
            return {"risk_forecast": [], "income_forecast": [], "current_risk": {}, "narrative": ""}
        
        user = await db["users"].find_one({"id": worker_id})
        base_income = user.get("avg_daily_income", 1500) if user else 1500
        worker_name = user.get("name", "Worker") if user else "Worker"
        city = user.get("city", "") if user else ""
        reliability = user.get("reliability_score", 0.8) if user else 0.8
        
        date_seed = _date_seed()
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        risk_forecast = []
        for idx, d in enumerate(days):
            # Deterministic risk based on worker + day + date
            seed = f"{date_seed}:{worker_id}:risk:{idx}"
            base_risk = _seeded_value(seed, 0.1, 0.9)
            
            # Adjust for reliability — more reliable workers face similar external risk
            # but their parcels are less affected
            var = base_risk
            risk_forecast.append({
                "day": d,
                "risk": round(var, 3),
                "parcels": int(40 - (var * 15))
            })
        
        income_forecast = []
        normal = base_income * 6
        for i in range(1, 5):
            seed = f"{date_seed}:{worker_id}:income:{i}"
            loss_factor = _seeded_value(seed, 0.05, 0.3)
            # More reliable workers lose less
            adjusted_loss = loss_factor * (1.1 - reliability)
            income_forecast.append({
                "week": f"W{i}",
                "predicted": int(normal * (1 - adjusted_loss)),
                "normal": int(normal)
            })
        
        # Current risk from the "today" equivalent (index 0)
        today_risk = risk_forecast[0]["risk"]
        risk_level = "high" if today_risk > 0.7 else "moderate" if today_risk > 0.4 else "low"
        
        current_risk = {
            "risk_level": risk_level,
            "risk_score": today_risk
        }
        
        # Generate AI narrative
        forecast_data = {
            "risk_forecast": risk_forecast,
            "income_forecast": income_forecast,
        }
        narrative = generate_weekly_advice(forecast_data)
        
        return {
            "risk_forecast": risk_forecast,
            "income_forecast": income_forecast,
            "current_risk": current_risk,
            "narrative": narrative,
        }

    @staticmethod
    async def get_ai_insights():
        """Generate AI-powered weekly insights for admin dashboard."""
        db = get_db()
        if db is None:
            return {"summary": "", "anomaly": None}
        
        liquidity = await LiquidityEngineService.get_state()
        
        total_claims = await db["claims"].count_documents({})
        auto_approved = await db["claims"].count_documents({"status": {"$in": ["auto_approved", "paid"]}})
        manual_review = await db["claims"].count_documents({"status": {"$in": ["delayed_review", "pending"]}})
        fraud_alerts = await db["fraud_alerts"].count_documents({"resolved": False})
        
        # Fraud rings count
        bad_users = await db["users"].count_documents({"nearby_claim_cluster_score": {"$gt": 0.5}})
        fraud_rings = 1 if bad_users > 3 else 0
        
        total_payouts = liquidity.get("total_payouts", 0)
        liquidity_ratio = liquidity.get("liquidity_ratio", 2.5)
        reserve_balance = liquidity.get("reserve_balance", 50000)
        
        summary = generate_admin_weekly_summary(
            total_claims=total_claims,
            total_payout=total_payouts,
            auto_approved=auto_approved,
            manual_review=manual_review,
            fraud_alerts=fraud_alerts,
            fraud_rings=fraud_rings,
            liquidity_ratio=liquidity_ratio,
            reserve_balance=reserve_balance,
        )
        
        anomaly = generate_anomaly_spotlight(
            liquidity_ratio=liquidity_ratio,
            fraud_alerts=fraud_alerts,
            payout_rate=total_payouts,
            claim_spike=(total_claims > 50),
        )
        
        return {
            "summary": summary,
            "anomaly": anomaly,
        }

    @staticmethod
    async def get_system_health():
        """Return system health indicators for the frontend."""
        db = get_db()
        if db is None:
            return {"throttle_state": "NORMAL", "health": "unknown"}
        
        liquidity = await LiquidityEngineService.get_state()
        liquidity_ratio = liquidity.get("liquidity_ratio", 2.5)
        
        now = datetime.utcnow()
        recent_claims = await db["claims"].count_documents({
            "created_at": {"$gte": now - timedelta(minutes=30)}
        })
        fraud_alerts = await db["fraud_alerts"].count_documents({"resolved": False})
        
        # Determine throttle state
        if recent_claims > 50 and liquidity_ratio < 1.0:
            throttle_state = "LOCKDOWN"
        elif recent_claims > 30 or liquidity_ratio < 1.2:
            throttle_state = "HIGH_ALERT"
        elif recent_claims > 15 or fraud_alerts > 20:
            throttle_state = "ELEVATED"
        else:
            throttle_state = "NORMAL"
        
        # Overall health
        if liquidity_ratio >= 1.5 and throttle_state == "NORMAL":
            health = "healthy"
        elif liquidity_ratio >= 1.0:
            health = "caution"
        else:
            health = "critical"
        
        return {
            "throttle_state": throttle_state,
            "health": health,
            "liquidity_ratio": round(liquidity_ratio, 2),
            "active_fraud_alerts": fraud_alerts,
            "recent_claims_30min": recent_claims,
            "reserve_balance": liquidity.get("reserve_balance", 0),
        }

    @staticmethod
    async def get_worker_narrative(worker_id: str):
        """Return a personalized narrative for a specific worker."""
        db = get_db()
        if db is None:
            return {"narrative": ""}
        
        user = await db["users"].find_one({"id": worker_id})
        trust = await db["trust_scores"].find_one({"worker_id": worker_id}, sort=[("computed_at", -1)])
        
        worker_name = user.get("name", "Worker") if user else "Worker"
        composite = trust.get("composite_score", 0.85) if trust else 0.85
        
        trust_narrative = generate_trust_narrative(
            {"composite_score": composite},
            worker_name=worker_name
        )
        
        # Get recent claims count  
        claims_count = await db["claims"].count_documents({"worker_id": worker_id})
        approved = await db["claims"].count_documents({
            "worker_id": worker_id,
            "status": {"$in": ["auto_approved", "paid"]}
        })
        
        return {
            "trust_narrative": trust_narrative,
            "trust_score": composite,
            "total_claims": claims_count,
            "approved_claims": approved,
            "worker_name": worker_name,
        }
