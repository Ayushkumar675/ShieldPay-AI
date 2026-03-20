"""
ShieldPay AI — Worker Management API
Registration, authentication, profile management.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime

from app.models.schemas import User, UserCreate, UserLogin, TokenResponse, UserRole
from app.models.database import get_db
from app.core.auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_admin
)

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_worker(user_data: UserCreate):
    """Register a new worker or admin."""
    db = get_db()
    existing = await db["users"].find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name=user_data.name,
        email=user_data.email,
        phone=user_data.phone,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        platform=user_data.platform,
        warehouse_id=user_data.warehouse_id,
    )

    await db["users"].insert_one(user.model_dump())

    token = create_access_token({
        "sub": user.id,
        "role": user.role,
        "email": user.email,
    })

    return TokenResponse(
        access_token=token,
        role=user.role,
        user_id=user.id,
        name=user.name,
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Authenticate worker/admin and return JWT token."""
    db = get_db()
    user = await db["users"].find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": user["id"],
        "role": user["role"],
        "email": user["email"],
    })

    return TokenResponse(
        access_token=token,
        role=user["role"],
        user_id=user["id"],
        name=user["name"],
    )


@router.get("/me")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile."""
    db = get_db()
    user = await db["users"].find_one({"id": current_user["user_id"]}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/dashboard")
async def worker_dashboard(current_user: dict = Depends(get_current_user)):
    """Get worker dashboard data — coverage, claims, income stats."""
    db = get_db()
    worker_id = current_user["user_id"]

    worker = await db["users"].find_one({"id": worker_id}, {"_id": 0, "password_hash": 0})
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    # Get active policy
    policy = await db["policies"].find_one(
        {"worker_id": worker_id, "status": "active"},
        {"_id": 0}
    )

    # Get recent claims
    claims_cursor = db["claims"].find(
        {"worker_id": worker_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(10)
    recent_claims = await claims_cursor.to_list(length=10)

    # Get recent payments
    payments_cursor = db["payouts"].find(
        {"worker_id": worker_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(10)
    recent_payments = await payments_cursor.to_list(length=10)

    # Count stats
    total_claims = await db["claims"].count_documents({"worker_id": worker_id})
    approved_claims = await db["claims"].count_documents({
        "worker_id": worker_id,
        "status": {"$in": ["approved", "auto_approved", "paid"]}
    })

    return {
        "worker": worker,
        "active_policy": policy,
        "recent_claims": recent_claims,
        "recent_payments": recent_payments,
        "stats": {
            "total_claims": total_claims,
            "approved_claims": approved_claims,
            "weekly_insured_income": policy["coverage_amount"] if policy else 0,
            "reliability_score": worker.get("reliability_score", 1.0),
        }
    }


@router.get("/list")
async def list_workers(
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(require_admin)
):
    """Admin: List all workers with pagination."""
    db = get_db()
    cursor = db["users"].find(
        {"role": "worker"},
        {"_id": 0, "password_hash": 0}
    ).skip(skip).limit(limit)
    workers = await cursor.to_list(length=limit)
    total = await db["users"].count_documents({"role": "worker"})
    return {"workers": workers, "total": total, "skip": skip, "limit": limit}
