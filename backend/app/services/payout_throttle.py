"""
ShieldPay AI — Adaptive Payout Throttling & Liquidity Protection
================================================================
Graduated throttle states with named levels and auto-escalation.
Prevents liquidity drain during coordinated fraud attacks.

Throttle States:
  NORMAL     → Full payouts, all systems nominal
  ELEVATED   → Minor restrictions, increased monitoring
  HIGH_ALERT → Significant reduction, most claims soft-verified
  LOCKDOWN   → Emergency mode, all payouts frozen pending review
"""
from datetime import datetime, timedelta
from typing import Dict

from app.core.config import settings


# ─── Throttle State Definitions ──────────────────────────

THROTTLE_STATES = {
    "NORMAL": {
        "payout_multiplier": 1.0,
        "description": "All systems operational. Payouts processing normally.",
        "color": "#10b981",  # green
    },
    "ELEVATED": {
        "payout_multiplier": 0.85,
        "description": "Slight payout reduction. Increased monitoring active.",
        "color": "#f59e0b",  # amber
    },
    "HIGH_ALERT": {
        "payout_multiplier": 0.50,
        "description": "Significant payout reduction. Most claims require verification.",
        "color": "#ef4444",  # red
    },
    "LOCKDOWN": {
        "payout_multiplier": 0.0,
        "description": "Emergency lockdown. All payouts frozen pending manual review.",
        "color": "#dc2626",  # dark red
    },
}


async def check_throttle() -> Dict:
    """
    Determine current throttle state based on multiple signals.

    Triggers:
    1. Payout rate exceeds 3x normal in last hour
    2. Claim spike detected (>50 claims in 30 min)
    3. Liquidity ratio drops below reserve threshold
    4. Cross-signal: multiple triggers compound
    """
    from app.models.database import get_db
    db = get_db()

    if db is None:
        return {
            "state": "NORMAL",
            "is_throttled": False,
            "payout_multiplier": 1.0,
            "description": THROTTLE_STATES["NORMAL"]["description"],
            "color": THROTTLE_STATES["NORMAL"]["color"],
            "reason": "no_db",
            "metrics": {},
        }

    now = datetime.utcnow()

    # Check 1: Claim spike in last 30 minutes
    recent_claims = await db["claims"].count_documents({
        "created_at": {"$gte": now - timedelta(minutes=30)}
    })
    claim_spike = recent_claims > 50
    claim_elevated = recent_claims > 15

    # Check 2: Payout rate in last hour
    hour_payouts = await db["payouts"].aggregate([
        {"$match": {
            "type": "claim_payout",
            "created_at": {"$gte": now - timedelta(hours=1)}
        }},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}
    ]).to_list(1)

    hour_payout_total = hour_payouts[0]["total"] if hour_payouts else 0
    hour_payout_count = hour_payouts[0]["count"] if hour_payouts else 0
    payout_rate_spike = hour_payout_count > 20
    payout_elevated = hour_payout_count > 8

    # Check 3: Overall liquidity
    total_premiums_result = await db["payouts"].aggregate([
        {"$match": {"type": "premium_collected"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    total_payouts_result = await db["payouts"].aggregate([
        {"$match": {"type": "claim_payout"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)

    total_premiums = total_premiums_result[0]["total"] if total_premiums_result else 0
    total_payouts = total_payouts_result[0]["total"] if total_payouts_result else 0
    liquidity_ratio = total_premiums / max(total_payouts, 1)
    low_liquidity = liquidity_ratio < (1 + settings.LIQUIDITY_RESERVE_RATIO)
    critical_liquidity = liquidity_ratio < 0.8

    # Check 4: Fraud alert surge
    recent_fraud = await db["fraud_alerts"].count_documents({
        "created_at": {"$gte": now - timedelta(hours=1)},
        "resolved": False,
    })
    fraud_surge = recent_fraud > 10

    # ─── Determine State ──────────────────────────────────
    threat_score = 0

    if claim_spike:
        threat_score += 3
    elif claim_elevated:
        threat_score += 1

    if payout_rate_spike:
        threat_score += 3
    elif payout_elevated:
        threat_score += 1

    if critical_liquidity:
        threat_score += 4
    elif low_liquidity:
        threat_score += 2

    if fraud_surge:
        threat_score += 2

    # Map threat score to state
    if threat_score >= 7:
        state = "LOCKDOWN"
        reason = "Multiple critical threats detected simultaneously"
    elif threat_score >= 4:
        state = "HIGH_ALERT"
        reasons = []
        if claim_spike:
            reasons.append("claim spike")
        if payout_rate_spike:
            reasons.append("payout rate spike")
        if low_liquidity:
            reasons.append("low liquidity")
        if fraud_surge:
            reasons.append("fraud surge")
        reason = " + ".join(reasons)
    elif threat_score >= 2:
        state = "ELEVATED"
        reason = "Elevated activity detected"
    else:
        state = "NORMAL"
        reason = "normal"

    state_config = THROTTLE_STATES[state]

    return {
        "state": state,
        "is_throttled": state != "NORMAL",
        "payout_multiplier": state_config["payout_multiplier"],
        "description": state_config["description"],
        "color": state_config["color"],
        "reason": reason,
        "threat_score": threat_score,
        "metrics": {
            "recent_claims_30min": recent_claims,
            "hour_payout_total": round(hour_payout_total, 2),
            "hour_payout_count": hour_payout_count,
            "liquidity_ratio": round(liquidity_ratio, 3),
            "total_premiums": round(total_premiums, 2),
            "total_payouts": round(total_payouts, 2),
            "recent_fraud_alerts": recent_fraud,
        },
    }


async def get_liquidity_simulation() -> Dict:
    """Simulate liquidity projections based on current trends."""
    from app.models.database import get_db
    db = get_db()

    if db is None:
        return {"error": "Database not connected"}

    pipeline = [
        {"$group": {
            "_id": {
                "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "type": "$type"
            },
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.date": 1}}
    ]
    results = await db["payouts"].aggregate(pipeline).to_list(100)

    daily_data = {}
    for r in results:
        date = r["_id"]["date"]
        if date not in daily_data:
            daily_data[date] = {"premiums": 0, "payouts": 0}
        if r["_id"]["type"] == "premium_collected":
            daily_data[date]["premiums"] = round(r["total"], 2)
        else:
            daily_data[date]["payouts"] = round(r["total"], 2)

    running_balance = 0
    timeline = []
    for date in sorted(daily_data.keys()):
        d = daily_data[date]
        running_balance += d["premiums"] - d["payouts"]
        timeline.append({
            "date": date,
            "premiums": d["premiums"],
            "payouts": d["payouts"],
            "net": round(d["premiums"] - d["payouts"], 2),
            "running_balance": round(running_balance, 2),
        })

    return {
        "timeline": timeline,
        "current_balance": round(running_balance, 2),
        "health": "healthy" if running_balance > 0 else "critical",
    }
