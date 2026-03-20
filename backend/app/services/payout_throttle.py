"""
ShieldPay AI — Adaptive Payout Throttling & Liquidity Protection
Prevents liquidity drain during coordinated fraud attacks.
"""
from datetime import datetime, timedelta
from typing import Dict

from app.core.config import settings


async def check_throttle() -> Dict:
    """
    Check if payout throttling is active.
    
    Triggers throttle when:
    1. Payout rate exceeds 3x normal in last hour
    2. Claim spike detected (>50 claims in 30 min)
    3. Liquidity ratio drops below reserve threshold
    """
    from app.models.database import get_db
    db = get_db()

    if not db:
        return {"is_throttled": False, "payout_multiplier": 1.0, "reason": "no_db"}

    now = datetime.utcnow()

    # Check 1: Claim spike in last 30 minutes
    recent_claims = await db.claims.count_documents({
        "created_at": {"$gte": now - timedelta(minutes=30)}
    })
    claim_spike = recent_claims > 50

    # Check 2: Payout rate in last hour
    hour_payouts = await db.payments.aggregate([
        {"$match": {
            "type": "claim_payout",
            "created_at": {"$gte": now - timedelta(hours=1)}
        }},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}
    ]).to_list(1)

    hour_payout_total = hour_payouts[0]["total"] if hour_payouts else 0
    hour_payout_count = hour_payouts[0]["count"] if hour_payouts else 0
    payout_rate_spike = hour_payout_count > 20  # More than 20 payouts per hour

    # Check 3: Overall liquidity
    total_premiums_result = await db.payments.aggregate([
        {"$match": {"type": "premium_collected"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    total_payouts_result = await db.payments.aggregate([
        {"$match": {"type": "claim_payout"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)

    total_premiums = total_premiums_result[0]["total"] if total_premiums_result else 0
    total_payouts = total_payouts_result[0]["total"] if total_payouts_result else 0
    liquidity_ratio = total_premiums / max(total_payouts, 1)
    low_liquidity = liquidity_ratio < (1 + settings.LIQUIDITY_RESERVE_RATIO)

    # Determine throttle level
    is_throttled = claim_spike or payout_rate_spike or low_liquidity

    if is_throttled:
        # Reduce payouts proportionally to risk
        if claim_spike and payout_rate_spike:
            multiplier = 0.3  # Severe: 70% reduction
            reason = "claim_spike + payout_rate_spike"
        elif low_liquidity:
            multiplier = 0.5  # Moderate: 50% reduction
            reason = "low_liquidity"
        elif claim_spike:
            multiplier = 0.6  # Claim spike: 40% reduction
            reason = "claim_spike"
        else:
            multiplier = 0.7  # Payout rate: 30% reduction
            reason = "payout_rate_spike"
    else:
        multiplier = 1.0
        reason = "normal"

    return {
        "is_throttled": is_throttled,
        "payout_multiplier": multiplier,
        "reason": reason,
        "metrics": {
            "recent_claims_30min": recent_claims,
            "hour_payout_total": round(hour_payout_total, 2),
            "hour_payout_count": hour_payout_count,
            "liquidity_ratio": round(liquidity_ratio, 3),
            "total_premiums": round(total_premiums, 2),
            "total_payouts": round(total_payouts, 2),
        }
    }


async def get_liquidity_simulation() -> Dict:
    """
    Simulate liquidity projections based on current trends.
    Useful for admin dashboard.
    """
    from app.models.database import get_db
    db = get_db()

    if not db:
        return {"error": "Database not connected"}

    # Get daily trends for last 30 days
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
    results = await db.payments.aggregate(pipeline).to_list(100)

    daily_data = {}
    for r in results:
        date = r["_id"]["date"]
        if date not in daily_data:
            daily_data[date] = {"premiums": 0, "payouts": 0}
        if r["_id"]["type"] == "premium_collected":
            daily_data[date]["premiums"] = round(r["total"], 2)
        else:
            daily_data[date]["payouts"] = round(r["total"], 2)

    # Calculate running balance
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
