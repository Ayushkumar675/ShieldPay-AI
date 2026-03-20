"""
ShieldPay AI — Premium Pricing API
Dynamic weekly premium calculation endpoint.
"""
from fastapi import APIRouter, Depends

from app.models.database import get_db
from app.core.auth import get_current_user
from app.ai.premium_optimizer import calculate_premium

router = APIRouter()


@router.get("/calculate")
async def get_premium_quote(current_user: dict = Depends(get_current_user)):
    """Get a dynamic premium quote for the current worker."""
    db = get_db()
    worker = await db.users.find_one({"id": current_user["user_id"]})
    if not worker:
        return {"error": "Worker not found"}

    result = await calculate_premium(worker)
    return {
        "premium_quote": result,
        "formula": "premium = base_price + (predicted_income_volatility × risk_multiplier)",
    }


@router.get("/factors")
async def get_premium_factors(current_user: dict = Depends(get_current_user)):
    """Get breakdown of risk factors affecting premium."""
    db = get_db()
    worker = await db.users.find_one({"id": current_user["user_id"]})
    if not worker:
        return {"error": "Worker not found"}

    from app.ai.risk_engine import get_risk_factors
    factors = await get_risk_factors(worker.get("warehouse_id", ""), worker.get("home_location", {}))
    return {"risk_factors": factors}
