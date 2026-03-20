"""
ShieldPay AI — Database & Pydantic Schemas
MongoDB document models for all platform entities.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid


# ─── Enums ────────────────────────────────────────────────

class UserRole(str, Enum):
    WORKER = "worker"
    ADMIN = "admin"


class PolicyStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ClaimStatus(str, Enum):
    PENDING = "pending"
    AUTO_APPROVED = "auto_approved"
    SOFT_VERIFY = "soft_verify"
    DELAYED_REVIEW = "delayed_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class DisruptionType(str, Enum):
    WEATHER = "weather"
    WAREHOUSE_SHUTDOWN = "warehouse_shutdown"
    CURFEW_LOCKDOWN = "curfew_lockdown"
    TRAFFIC_GRIDLOCK = "traffic_gridlock"
    PARCEL_DROP = "parcel_allocation_drop"


class PayoutTier(str, Enum):
    INSTANT = "instant"
    SOFT_VERIFY = "soft_verify"
    DELAYED = "delayed"


# ─── Helper ───────────────────────────────────────────────

def generate_id() -> str:
    return str(uuid.uuid4())


# ─── User / Worker ───────────────────────────────────────

class GeoLocation(BaseModel):
    lat: float
    lng: float
    city: str = ""
    zone: str = ""  # delivery zone ID


class DeviceSignals(BaseModel):
    is_emulator: bool = False
    is_rooted: bool = False
    app_install_age_days: int = 0
    background_location_streaming: bool = False
    accelerometer_available: bool = True


class User(BaseModel):
    id: str = Field(default_factory=generate_id)
    name: str
    email: str
    phone: str
    password_hash: str
    role: UserRole = UserRole.WORKER
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Worker-specific fields
    platform: str = ""  # amazon, flipkart, etc.
    warehouse_id: str = ""
    home_location: Optional[GeoLocation] = None
    device_signals: Optional[DeviceSignals] = None
    avg_daily_parcels: float = 0.0
    avg_daily_income: float = 0.0
    reliability_score: float = 1.0  # 0-1 reward score
    is_active: bool = True


class UserCreate(BaseModel):
    name: str
    email: str
    phone: str
    password: str
    role: UserRole = UserRole.WORKER
    platform: str = ""
    warehouse_id: str = ""


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    user_id: str
    name: str


# ─── Policy ──────────────────────────────────────────────

class Policy(BaseModel):
    id: str = Field(default_factory=generate_id)
    worker_id: str
    status: PolicyStatus = PolicyStatus.ACTIVE
    coverage_amount: float  # max payout per week in ₹
    premium_amount: float  # weekly premium in ₹
    risk_score: float = 0.0
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None
    auto_renew: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PolicyCreate(BaseModel):
    coverage_amount: float = 2000.0  # default ₹2000 coverage


# ─── Disruption Trigger ─────────────────────────────────

class DisruptionTrigger(BaseModel):
    id: str = Field(default_factory=generate_id)
    type: DisruptionType
    severity: float  # 0-1
    affected_zone: str
    affected_warehouse_ids: List[str] = []
    location: GeoLocation
    description: str = ""
    weather_data: Optional[dict] = None
    traffic_data: Optional[dict] = None
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    is_active: bool = True


# ─── Trust Score ─────────────────────────────────────────

class TrustScore(BaseModel):
    worker_id: str
    real_movement_score: float = 1.0     # 0-1
    delivery_activity_score: float = 1.0  # 0-1
    environmental_match_score: float = 1.0  # 0-1
    historical_trust_index: float = 1.0   # 0-1
    fraud_anomaly_score: float = 0.0      # 0-1 (higher = more fraud)
    composite_score: float = 1.0          # weighted final
    computed_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Claim ───────────────────────────────────────────────

class Claim(BaseModel):
    id: str = Field(default_factory=generate_id)
    worker_id: str
    policy_id: str
    trigger_id: str
    status: ClaimStatus = ClaimStatus.PENDING
    payout_tier: PayoutTier = PayoutTier.DELAYED
    disruption_type: DisruptionType = DisruptionType.WEATHER
    estimated_income_loss: float = 0.0
    payout_amount: float = 0.0
    trust_score: Optional[TrustScore] = None
    worker_confirmation: Optional[bool] = None  # for soft-verify
    admin_notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None


# ─── Fraud Analysis ─────────────────────────────────────

class FraudAlert(BaseModel):
    id: str = Field(default_factory=generate_id)
    worker_id: str
    alert_type: str  # gps_spoof, claim_spike, ring_detected, emulator, teleport
    severity: float  # 0-1
    details: dict = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = False



# ─── Financials ──────────────────────────────────────────

class PayoutTransaction(BaseModel):
    id: str = Field(default_factory=generate_id)
    claim_id: str
    worker_id: str
    amount: float
    status: str = "processed"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class LiquidityState(BaseModel):
    total_premiums: float = 0.0
    total_payouts: float = 0.0
    reserve_balance: float = 50000.0  # Initial seed capital
    liquidity_ratio: float = 1.0
    active_policies_count: int = 0
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Payout ────────────────────────────────────────────

class Payout(BaseModel):
    id: str = Field(default_factory=generate_id)
    worker_id: str
    type: str  # premium_collected, claim_payout
    amount: float
    status: str = "completed"  # completed, pending, failed
    reference_id: str = ""  # claim_id or policy_id
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Analytics ───────────────────────────────────────────

class PlatformAnalytics(BaseModel):
    total_workers: int = 0
    active_policies: int = 0
    total_premiums_collected: float = 0.0
    total_payouts: float = 0.0
    liquidity_ratio: float = 1.0
    avg_trust_score: float = 1.0
    fraud_alerts_today: int = 0
    active_disruptions: int = 0
