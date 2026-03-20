"""
ShieldPay AI — Claims API
"""
from fastapi import APIRouter, HTTPException, Path
from datetime import datetime
from app.models.database import get_db
from app.models.schemas import ClaimStatus
from app.services.liquidity_engine import LiquidityEngineService
from typing import Optional

router = APIRouter()

@router.get("/")
async def get_claims(limit: int = 50):
    """Fetch recent claims."""
    db = get_db()
    
    # Simple query to get latest claims
    cursor = db["claims"].find().sort("created_at", -1).limit(limit)
    claims = await cursor.to_list(length=limit)
    
    # Serialize object IDs and Datetimes
    serialized_claims = []
    for c in claims:
        ser = c.copy()
        ser["id"] = str(c.get("id"))
        if "_id" in ser:
            ser["_id"] = str(ser["_id"])
        if ser.get("created_at"):
            ser["created_at"] = str(ser["created_at"])
        if ser.get("resolved_at"):
            ser["resolved_at"] = str(ser["resolved_at"])
        serialized_claims.append(ser)
            
    return serialized_claims

@router.post("/{claim_id}/confirm")
async def confirm_claim(claim_id: str = Path(..., title="The ID of the claim to confirm")):
    """
    Manually confirm a pending/soft-verify claim.
    Triggers payout and updates liquidity.
    """
    db = get_db()
    
    # 1. Find Claim via 'id' field (UUID)
    claim = await db["claims"].find_one({"id": claim_id})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
        
    current_status = claim.get("status")
    # Allowed statuses to confirm
    allowed = [
        ClaimStatus.SOFT_VERIFY, 
        ClaimStatus.DELAYED_REVIEW, 
        ClaimStatus.PENDING,
        "soft_verify", "delayed_review", "pending" # strings
    ]
    
    if current_status not in allowed:
        # If it's already approved/paid, fine, just return success
        if current_status in [ClaimStatus.APPROVED, ClaimStatus.PAID, "approved", "paid"]:
             return {"status": "success", "message": "Claim already processed."}
        raise HTTPException(status_code=400, detail=f"Claim status '{current_status}' cannot be confirmed.")

    # 2. Update Status -> Approved
    amount = claim.get("payout_amount", 0.0)
    worker_id = claim.get("worker_id")
    
    # Update claim status
    await db["claims"].update_one(
        {"id": claim_id},
        {
            "$set": {
                "status": ClaimStatus.APPROVED,
                "resolved_at": datetime.utcnow(),
            }
        }
    )
    
    # 3. Process Payout & Liquidity
    await LiquidityEngineService.update_on_payout(amount, claim_id, worker_id)
    
    return {
        "status": "success",
        "message": f"Claim {claim_id} confirmed. Payout of ₹{amount} processed.",
        "payout_amount": amount,
        "new_status": ClaimStatus.APPROVED
    }
