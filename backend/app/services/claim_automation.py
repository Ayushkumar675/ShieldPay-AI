"""
ShieldPay AI — Claim Automation Service
Parametric claim flow: trigger → trust → fraud → approval/verify/delay → payout
"""
from datetime import datetime
from typing import Dict

from app.models.schemas import Claim, ClaimStatus, PayoutTier, Payment
from app.core.config import settings


async def auto_create_claim(worker_id: str, policy_id: str, trigger: Dict):
    """
    Automatically create a claim when a parametric trigger is detected.
    
    Flow:
    1. Disruption Trigger Detected
    2. Trust Score Evaluation
    3. Fraud Risk Layer
    4. Claim Auto Approval / Soft Verification / Delayed Review
    5. Instant Payout Simulation
    """
    from app.models.database import get_db
    from app.ai.trust_scorer import compute_trust_score
    from app.ai.income_forecast import estimate_income_loss
    from app.services.payout_throttle import check_throttle

    db = get_db()
    if not db:
        return

    # Step 1: Compute trust score
    trust = await compute_trust_score(worker_id)

    # Step 2: Check payout throttle (liquidity protection)
    throttle = await check_throttle()

    # Step 3: Estimate income loss
    income_loss = await estimate_income_loss(worker_id, trigger)

    # Step 4: Get policy coverage
    policy = await db.policies.find_one({"id": policy_id})
    max_payout = min(income_loss, policy["coverage_amount"], settings.MAX_WEEKLY_PAYOUT)

    # Step 5: Apply throttle reduction if active
    if throttle["is_throttled"]:
        max_payout = max_payout * throttle["payout_multiplier"]

    # Step 6: Determine payout tier
    composite = trust.composite_score

    if composite >= settings.TRUST_INSTANT_PAYOUT and not throttle["is_throttled"]:
        payout_tier = PayoutTier.INSTANT
        claim_status = ClaimStatus.AUTO_APPROVED
        payout_amount = max_payout
    elif composite >= settings.TRUST_SOFT_VERIFY:
        payout_tier = PayoutTier.SOFT_VERIFY
        claim_status = ClaimStatus.SOFT_VERIFY
        payout_amount = 0  # Awaiting confirmation
    else:
        payout_tier = PayoutTier.DELAYED
        claim_status = ClaimStatus.DELAYED_REVIEW
        payout_amount = 0  # Awaiting admin review

    # Step 7: Create claim record
    claim = Claim(
        worker_id=worker_id,
        policy_id=policy_id,
        trigger_id=trigger["id"],
        status=claim_status,
        payout_tier=payout_tier,
        disruption_type=trigger.get("type", "weather"),
        estimated_income_loss=income_loss,
        payout_amount=round(payout_amount, 2),
        trust_score=trust,
    )

    await db.claims.insert_one(claim.model_dump())

    # Step 8: Process instant payout
    if claim_status == ClaimStatus.AUTO_APPROVED:
        payment = Payment(
            worker_id=worker_id,
            type="claim_payout",
            amount=round(payout_amount, 2),
            reference_id=claim.id,
        )
        await db.payments.insert_one(payment.model_dump())
        await db.claims.update_one(
            {"id": claim.id},
            {"$set": {
                "status": ClaimStatus.PAID,
                "payout_amount": round(payout_amount, 2),
                "resolved_at": datetime.utcnow(),
            }}
        )

    # Step 9: Update worker reliability score
    if trust.fraud_anomaly_score > 0.5:
        # Decrease reliability for suspicious workers
        await db.users.update_one(
            {"id": worker_id},
            {"$mul": {"reliability_score": 0.95}}
        )
    elif trust.composite_score > 0.85:
        # Reward trustworthy workers
        await db.users.update_one(
            {"id": worker_id},
            {"$min": {"reliability_score": 1.0}},
        )
        await db.users.update_one(
            {"id": worker_id},
            {"$mul": {"reliability_score": 1.01}},
        )

    return claim.model_dump()
