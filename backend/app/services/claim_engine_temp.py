"""
ShieldPay AI — Full Lifecycle Claim Automation Engine
"""
import uuid
from datetime import datetime
from typing import Dict, Any

from app.models.schemas import Claim, ClaimStatus, PayoutTier, Payout, DisruptionTrigger, DisruptionType, GeoLocation
from app.models.database import get_db
from app.core.config import settings
from app.ai.trust_scorer import compute_trust_score
from app.ai.income_forecast import estimate_income_loss
from app.ai.risk_engine import compute_composite_risk
from app.services.liquidity_engine import LiquidityEngineService
import logging

logger = logging.getLogger("claim_engine")
logger.setLevel(logging.INFO)

class ClaimEngineService:
    @staticmethod
    async def process_disruption_event(trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        1. Receive disruption trigger input
        2. Fetch active policies from database
        3. Run AI risk prediction
        4. Run fraud anomaly detection
        5. Compute trust score
        6. Decide payout tier
        7. Create claim record
        8. If instant payout -> create payout record
        9. Update insurer liquidity metrics
        """
        db = get_db()
        if not db:
            raise Exception("Database access failed")

        disruption_id = str(uuid.uuid4())
        disruption_type_str = trigger_data.get("disruption_type", "weather")
        city = trigger_data.get("city", "Unknown")
        severity = float(trigger_data.get("severity", 0.5))

        # Handle valid enum types or default
        try:
            dtype = DisruptionType(disruption_type_str)
        except ValueError:
            dtype = DisruptionType.WEATHER

        # 1. Create Disruption Record
        trigger_record = DisruptionTrigger(
            id=disruption_id,
            type=dtype,
            severity=severity,
            affected_zone=city,
            location=GeoLocation(lat=0.0, lng=0.0, city=city, zone=city),
            description=f"{disruption_type_str.capitalize()} detected in {city} with severity {severity}"
        )
        await db["disruptions"].insert_one(trigger_record.model_dump())
        logger.info(f"Disruption detected: {dtype.value} in {city} (severity: {severity})")

        # 2. Fetch active policies
        active_policies_cursor = db["policies"].find({"status": "active"})
        policies = await active_policies_cursor.to_list(length=1000)

        processed_claims = []
        total_payout_amount = 0.0

        for policy in policies:
            worker_id = policy["worker_id"]
            user = await db["users"].find_one({"id": worker_id})
            if not user:
                continue

            home_loc = user.get("home_location", {})
            user_city = home_loc.get("city", "")

            # Filter by affected city. Be lenient if no city info exists on user
            if city and user_city and city.lower() != user_city.lower():
                continue

            # 3. AI Risk Prediction
            warehouse_id = user.get("warehouse_id", "default")
            avg_parcels = user.get("avg_daily_parcels", 30)
            await compute_composite_risk(warehouse_id=warehouse_id, city=city, avg_daily_parcels=avg_parcels)

            # 4 & 5. Fraud Anomaly Detection & Trust Score
            trust = await compute_trust_score(worker_id)
            if float(getattr(trust, "fraud_anomaly_score", 0.0)) > 0.6:
                logger.warning(f"Fraud anomaly triggered for worker {worker_id} (score: {trust.fraud_anomaly_score})")
            
            # Predict Income Loss based on disruption
            income_loss = await estimate_income_loss(worker_id, trigger_record.model_dump())
            
            # 6. Decide Payout Tier
            max_payout = min(income_loss, policy.get("coverage_amount", 2000), settings.MAX_WEEKLY_PAYOUT)
            composite = trust.composite_score

            claim_status = ClaimStatus.PENDING
            payout_tier = PayoutTier.DELAYED
            payout_amount = 0.0

            if composite >= settings.TRUST_INSTANT_PAYOUT:
                payout_tier = PayoutTier.INSTANT
                claim_status = ClaimStatus.AUTO_APPROVED
                payout_amount = max_payout
            elif composite >= settings.TRUST_SOFT_VERIFY:
                payout_tier = PayoutTier.SOFT_VERIFY
                claim_status = ClaimStatus.SOFT_VERIFY
                payout_amount = max_payout
            else:
                payout_tier = PayoutTier.DELAYED
                claim_status = ClaimStatus.DELAYED_REVIEW
                payout_amount = max_payout  # pending review

            # 7. Create Claim Record
            claim = Claim(
                id=str(uuid.uuid4()),
                worker_id=worker_id,
                policy_id=policy.get("id"),
                trigger_id=disruption_id,
                status=claim_status,
                payout_tier=payout_tier,
                disruption_type=dtype,
                estimated_income_loss=round(income_loss, 2),
                payout_amount=round(payout_amount, 2),
                trust_score=trust,
                created_at=datetime.utcnow()
            )
            
            await db["claims"].insert_one(claim.model_dump())
            
            # 8. If Instant -> Process Payout immediately
            if claim_status == ClaimStatus.AUTO_APPROVED:
                await LiquidityEngineService.update_on_payout(payout_amount, claim.id, worker_id)
                total_payout_amount += payout_amount

            processed_claims.append({
                "worker_name": user.get("name"),
                "status": claim_status,
                "tier": payout_tier,
                "amount": round(payout_amount, 2),
                "trust": round(composite, 2)
            })

        # 9. Return Summary
        return {
            "disruption_id": disruption_id,
            "total_claims": len(processed_claims),
            "instant_payouts": len([c for c in processed_claims if c["status"] == ClaimStatus.AUTO_APPROVED]),
            "total_payout_value": round(total_payout_amount, 2),
            "affected_workers": processed_claims
        }
