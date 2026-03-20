"""
ShieldPay AI — Claims Processing API
Parametric claim submission, auto-approval flow, status tracking.
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Optional

from app.models.schemas import Claim, ClaimStatus, PayoutTier, DisruptionType, Payment
from app.models.database import get_db
from app.core.auth import get_current_user, require_admin
from app.core.config import settings

router = APIRouter()


@router.post("/submit")
async def submit_claim(
    trigger_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Submit a claim against an active disruption trigger."""
    db = get_db()
    worker_id = current_user["user_id"]

    # Verify active policy
    policy = await db.policies.find_one({"worker_id": worker_id, "status": "active"})
    if not policy:
        raise HTTPException(status_code=400, detail="No active policy. Purchase coverage first.")

    # Verify trigger exists
    trigger = await db.disruption_triggers.find_one({"id": trigger_id})
    if not trigger:
        raise HTTPException(status_code=404, detail="Disruption trigger not found")

    # Check for duplicate claim
    existing_claim = await db.claims.find_one({
        "worker_id": worker_id,
        "trigger_id": trigger_id,
    })
    if existing_claim:
        raise HTTPException(status_code=400, detail="Claim already submitted for this disruption")

    # Calculate trust score
    from app.ai.trust_scorer import compute_trust_score
    trust = await compute_trust_score(worker_id)

    # Determine payout tier based on trust score
    if trust.composite_score >= settings.TRUST_INSTANT_PAYOUT:
        payout_tier = PayoutTier.INSTANT
        claim_status = ClaimStatus.AUTO_APPROVED
    elif trust.composite_score >= settings.TRUST_SOFT_VERIFY:
        payout_tier = PayoutTier.SOFT_VERIFY
        claim_status = ClaimStatus.SOFT_VERIFY
    else:
        payout_tier = PayoutTier.DELAYED
        claim_status = ClaimStatus.DELAYED_REVIEW

    # Estimate income loss
    from app.ai.income_forecast import estimate_income_loss
    income_loss = await estimate_income_loss(worker_id, trigger)

    # Calculate payout (capped)
    payout_amount = min(income_loss, policy["coverage_amount"], settings.MAX_WEEKLY_PAYOUT)

    claim = Claim(
        worker_id=worker_id,
        policy_id=policy["id"],
        trigger_id=trigger_id,
        status=claim_status,
        payout_tier=payout_tier,
        disruption_type=trigger.get("type", DisruptionType.WEATHER),
        estimated_income_loss=income_loss,
        payout_amount=payout_amount if claim_status == ClaimStatus.AUTO_APPROVED else 0,
        trust_score=trust,
    )

    await db.claims.insert_one(claim.model_dump())

    # If auto-approved, process instant payout
    if claim_status == ClaimStatus.AUTO_APPROVED:
        payment = Payment(
            worker_id=worker_id,
            type="claim_payout",
            amount=payout_amount,
            reference_id=claim.id,
        )
        await db.payments.insert_one(payment.model_dump())
        await db.claims.update_one(
            {"id": claim.id},
            {"$set": {"status": ClaimStatus.PAID, "payout_amount": payout_amount, "resolved_at": datetime.utcnow()}}
        )

    return {
        "claim": claim.model_dump(),
        "trust_score": trust.model_dump(),
        "payout_tier": payout_tier,
        "message": _tier_message(payout_tier, payout_amount),
    }


@router.post("/{claim_id}/confirm")
async def confirm_soft_verify(
    claim_id: str,
    confirmed: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """Worker confirms a soft-verification claim."""
    db = get_db()
    claim = await db.claims.find_one({"id": claim_id, "worker_id": current_user["user_id"]})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim["status"] != ClaimStatus.SOFT_VERIFY:
        raise HTTPException(status_code=400, detail="Claim is not in soft verification status")

    if confirmed:
        policy = await db.policies.find_one({"id": claim["policy_id"]})
        payout = min(claim["estimated_income_loss"], policy["coverage_amount"], settings.MAX_WEEKLY_PAYOUT)

        await db.claims.update_one(
            {"id": claim_id},
            {"$set": {
                "status": ClaimStatus.PAID,
                "worker_confirmation": True,
                "payout_amount": payout,
                "resolved_at": datetime.utcnow(),
            }}
        )
        payment = Payment(
            worker_id=current_user["user_id"],
            type="claim_payout",
            amount=payout,
            reference_id=claim_id,
        )
        await db.payments.insert_one(payment.model_dump())
        return {"message": f"Claim confirmed! ₹{payout} payout processed.", "payout": payout}
    else:
        await db.claims.update_one(
            {"id": claim_id},
            {"$set": {"status": ClaimStatus.REJECTED, "worker_confirmation": False}}
        )
        return {"message": "Claim withdrawn by worker."}


@router.get("/my-claims")
async def get_my_claims(current_user: dict = Depends(get_current_user)):
    """Get all claims for the current worker."""
    db = get_db()
    cursor = db.claims.find(
        {"worker_id": current_user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1)
    claims = await cursor.to_list(length=50)
    return {"claims": claims}


@router.get("/all")
async def get_all_claims(
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(require_admin)
):
    """Admin: Get all claims with optional status filter."""
    db = get_db()
    query = {}
    if status_filter:
        query["status"] = status_filter

    cursor = db.claims.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    claims = await cursor.to_list(length=limit)
    total = await db.claims.count_documents(query)
    return {"claims": claims, "total": total}


@router.post("/{claim_id}/admin-review")
async def admin_claim_review(
    claim_id: str,
    approved: bool,
    notes: str = "",
    current_user: dict = Depends(require_admin)
):
    """Admin: Review and approve/reject a delayed claim."""
    db = get_db()
    claim = await db.claims.find_one({"id": claim_id})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    if approved:
        policy = await db.policies.find_one({"id": claim["policy_id"]})
        payout = min(claim["estimated_income_loss"], policy["coverage_amount"], settings.MAX_WEEKLY_PAYOUT)

        await db.claims.update_one(
            {"id": claim_id},
            {"$set": {
                "status": ClaimStatus.PAID,
                "payout_amount": payout,
                "admin_notes": notes,
                "resolved_at": datetime.utcnow(),
            }}
        )
        payment = Payment(
            worker_id=claim["worker_id"],
            type="claim_payout",
            amount=payout,
            reference_id=claim_id,
        )
        await db.payments.insert_one(payment.model_dump())
        return {"message": f"Claim approved. ₹{payout} payout processed.", "payout": payout}
    else:
        await db.claims.update_one(
            {"id": claim_id},
            {"$set": {"status": ClaimStatus.REJECTED, "admin_notes": notes, "resolved_at": datetime.utcnow()}}
        )
        return {"message": "Claim rejected."}


def _tier_message(tier: PayoutTier, amount: float) -> str:
    if tier == PayoutTier.INSTANT:
        return f"✅ Instant payout! ₹{amount} transferred to your account."
    elif tier == PayoutTier.SOFT_VERIFY:
        return "⚡ Quick verification needed. Please confirm your disruption in-app to receive payout."
    else:
        return "🔍 Your claim is under review. We'll process it within 24-48 hours for your protection."
