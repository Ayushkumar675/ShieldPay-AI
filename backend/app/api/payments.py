"""
ShieldPay AI — Payment Simulation API
Simulates premium collection and claim payouts.
"""
from fastapi import APIRouter, Depends
from datetime import datetime

from app.models.schemas import Payment
from app.models.database import get_db
from app.core.auth import get_current_user, require_admin

router = APIRouter()


@router.get("/history")
async def get_payment_history(current_user: dict = Depends(get_current_user)):
    """Get payment history for the current worker."""
    db = get_db()
    cursor = db.payments.find(
        {"worker_id": current_user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1)
    payments = await cursor.to_list(length=50)

    total_premiums = sum(p["amount"] for p in payments if p["type"] == "premium_collected")
    total_payouts = sum(p["amount"] for p in payments if p["type"] == "claim_payout")

    return {
        "payments": payments,
        "summary": {
            "total_premiums_paid": total_premiums,
            "total_payouts_received": total_payouts,
            "net_benefit": round(total_payouts - total_premiums, 2),
        }
    }


@router.get("/platform-summary")
async def get_platform_payment_summary(current_user: dict = Depends(require_admin)):
    """Admin: Get platform-wide payment summary."""
    db = get_db()

    premium_pipeline = [
        {"$match": {"type": "premium_collected"}},
        {"$group": {
            "_id": None,
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1},
        }}
    ]
    payout_pipeline = [
        {"$match": {"type": "claim_payout"}},
        {"$group": {
            "_id": None,
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1},
        }}
    ]

    premium_result = await db.payments.aggregate(premium_pipeline).to_list(1)
    payout_result = await db.payments.aggregate(payout_pipeline).to_list(1)

    premiums = premium_result[0] if premium_result else {"total": 0, "count": 0}
    payouts = payout_result[0] if payout_result else {"total": 0, "count": 0}

    total_premiums = premiums.get("total", 0)
    total_payouts = payouts.get("total", 0)

    return {
        "premiums": {
            "total_collected": total_premiums,
            "transaction_count": premiums.get("count", 0),
        },
        "payouts": {
            "total_disbursed": total_payouts,
            "transaction_count": payouts.get("count", 0),
        },
        "liquidity": {
            "reserve": round(total_premiums - total_payouts, 2),
            "ratio": round(total_premiums / max(total_payouts, 1), 3),
            "health": "healthy" if total_premiums > total_payouts * 1.3 else "warning" if total_premiums > total_payouts else "critical",
        }
    }
