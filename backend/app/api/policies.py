"""
ShieldPay AI — Policy Management API
Policy purchase, renewal, coverage status.
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta

from app.models.schemas import Policy, PolicyCreate, PolicyStatus
from app.models.database import get_db
from app.core.auth import get_current_user
from app.ai.premium_optimizer import calculate_premium

router = APIRouter()


@router.post("/purchase")
async def purchase_policy(
    policy_data: PolicyCreate,
    current_user: dict = Depends(get_current_user)
):
    """Purchase a new weekly micro-insurance policy."""
    db = get_db()
    worker_id = current_user["user_id"]

    # Check for existing active policy
    existing = await db.policies.find_one({"worker_id": worker_id, "status": "active"})
    if existing:
        raise HTTPException(status_code=400, detail="Active policy already exists. Cancel first or wait for expiry.")

    # Get worker data for premium calculation
    worker = await db.users.find_one({"id": worker_id})
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    # Calculate dynamic premium
    premium_result = await calculate_premium(worker)

    policy = Policy(
        worker_id=worker_id,
        coverage_amount=policy_data.coverage_amount,
        premium_amount=premium_result["premium"],
        risk_score=premium_result["risk_score"],
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=7),
    )

    await db.policies.insert_one(policy.model_dump())

    # Record premium payment
    from app.models.schemas import Payment
    payment = Payment(
        worker_id=worker_id,
        type="premium_collected",
        amount=premium_result["premium"],
        reference_id=policy.id,
    )
    await db.payments.insert_one(payment.model_dump())

    return {
        "policy": policy.model_dump(),
        "premium_breakdown": premium_result,
        "message": f"Policy activated! Coverage: ₹{policy.coverage_amount}/week, Premium: ₹{premium_result['premium']}/week"
    }


@router.get("/active")
async def get_active_policy(current_user: dict = Depends(get_current_user)):
    """Get current active policy for the worker."""
    db = get_db()
    policy = await db.policies.find_one(
        {"worker_id": current_user["user_id"], "status": "active"},
        {"_id": 0}
    )
    if not policy:
        return {"policy": None, "message": "No active policy found. Purchase one to get covered!"}
    return {"policy": policy}


@router.get("/history")
async def get_policy_history(current_user: dict = Depends(get_current_user)):
    """Get policy history for the worker."""
    db = get_db()
    cursor = db.policies.find(
        {"worker_id": current_user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1)
    policies = await cursor.to_list(length=50)
    return {"policies": policies}


@router.post("/{policy_id}/cancel")
async def cancel_policy(policy_id: str, current_user: dict = Depends(get_current_user)):
    """Cancel an active policy."""
    db = get_db()
    result = await db.policies.update_one(
        {"id": policy_id, "worker_id": current_user["user_id"], "status": "active"},
        {"$set": {"status": PolicyStatus.CANCELLED}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Active policy not found")
    return {"message": "Policy cancelled successfully"}
