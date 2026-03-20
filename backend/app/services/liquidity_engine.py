"""
ShieldPay AI — Financial Liquidity Engine
Manage reserves, premiums, payouts, and liquidity ratios.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.database import get_db
from app.models.schemas import LiquidityState, PayoutTransaction

class LiquidityEngineService:
    @staticmethod
    async def get_state() -> Dict[str, Any]:
        """Fetch current liquidity state or initialize if missing."""
        db = get_db()
        if db is None:
            return {}

        state_doc = await db["liquidity_state"].find_one({}, sort=[("last_updated", -1)])
        
        if not state_doc:
            # Fallback initialization
            state = {
                "reserve_balance": 50000.0,
                "total_premiums": 0.0,
                "total_payouts": 0.0,
                "liquidity_ratio": 2.5,
                "active_policies_count": 0,
                "last_updated": datetime.utcnow()
            }
            await db["liquidity_state"].insert_one(state)
            return state
        
        # Ensure ID is string for serialization
        if "_id" in state_doc:
            state_doc["_id"] = str(state_doc["_id"])
            
        return state_doc

    @staticmethod
    async def update_on_payout(amount: float, claim_id: str, worker_id: str):
        """Deduct payout from reserves and log transaction."""
        db = get_db()
        if db is None:
            return
        
        # 1. Update State
        state = await LiquidityEngineService.get_state()
        current_balance = state.get("reserve_balance", 0.0)
        current_payouts = state.get("total_payouts", 0.0)
        
        new_balance = current_balance - amount
        new_total_payouts = current_payouts + amount
        
        # Recalculate ratio (simplified: balance / expected_claims)
        # Assuming expected claims is roughly 20% of historical payouts + some buffer
        expected_claims = max(20000.0, new_total_payouts * 0.2)
        ratio = new_balance / expected_claims if expected_claims > 0 else 1.0
        
        await db["liquidity_state"].update_one(
            {},
            {
                "$set": {
                    "reserve_balance": new_balance,
                    "total_payouts": new_total_payouts,
                    "liquidity_ratio": round(ratio, 2),
                    "last_updated": datetime.utcnow()
                }
            },
            upsert=True
        )

        # 2. Log Transaction
        transaction = PayoutTransaction(
            claim_id=claim_id,
            worker_id=worker_id,
            amount=amount,
            status="processed"
        )
        await db["payout_transactions"].insert_one(transaction.model_dump())

    @staticmethod
    async def update_on_premium(amount: float):
        """Add premium to reserves."""
        db = get_db()
        if db is None:
            return

        state = await LiquidityEngineService.get_state()
        current_balance = state.get("reserve_balance", 0.0)
        current_premiums = state.get("total_premiums", 0.0)
        current_payouts = state.get("total_payouts", 0.0)
        
        new_balance = current_balance + amount
        new_total_premiums = current_premiums + amount
        
        # Recalculate ratio
        expected_claims = max(20000.0, current_payouts * 0.2)
        ratio = new_balance / expected_claims if expected_claims > 0 else 1.0

        await db["liquidity_state"].update_one(
            {},
            {
                "$set": {
                    "reserve_balance": new_balance,
                    "total_premiums": new_total_premiums,
                    "liquidity_ratio": round(ratio, 2),
                    "last_updated": datetime.utcnow()
                }
            },
            upsert=True
        )
