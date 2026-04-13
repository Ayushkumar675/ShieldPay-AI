"""
ShieldPay AI — Income Loss Forecast Model
Predicts expected reduction in parcel assignments for next 7 days.
Uses historical delivery data + current disruption context.

All projections use deterministic, date-seeded calculations
for consistent results within the same day.
"""
import hashlib
from datetime import datetime, timedelta
from typing import Dict


def _seeded_value(seed_str: str, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Generate a deterministic float from a seed string."""
    h = int(hashlib.sha256(seed_str.encode()).hexdigest()[:8], 16)
    normalized = (h % 10000) / 10000.0
    return min_val + normalized * (max_val - min_val)


def _date_seed() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


async def estimate_income_loss(worker_id: str, trigger: dict) -> float:
    """
    Estimate ₹ income loss for a worker based on a disruption trigger.
    
    Factors:
    - Worker's average daily income
    - Disruption severity (0-1)
    - Disruption type impact multiplier
    - Expected disruption duration
    """
    from app.models.database import get_db
    db = get_db()

    worker = await db["users"].find_one({"id": worker_id}) if db is not None else None

    avg_daily_income = worker.get("avg_daily_income", 500) if worker else 500
    severity = trigger.get("severity", 0.5)
    disruption_type = trigger.get("type", "weather")

    # Impact multiplier by disruption type
    type_impact = {
        "weather": 0.7,
        "warehouse_shutdown": 0.9,
        "curfew_lockdown": 0.85,
        "traffic_gridlock": 0.5,
        "parcel_allocation_drop": 0.6,
    }
    impact = type_impact.get(disruption_type, 0.6)

    # Deterministic duration based on severity
    if trigger.get("resolved_at") and trigger.get("detected_at"):
        try:
            detected = datetime.fromisoformat(str(trigger["detected_at"]))
            resolved = datetime.fromisoformat(str(trigger["resolved_at"]))
            duration_days = max(1, (resolved - detected).days)
        except (ValueError, TypeError):
            duration_days = max(1, int(severity * 7))
    else:
        duration_days = max(1, int(severity * 7))

    # Income loss = avg_daily × duration × impact
    income_loss = avg_daily_income * duration_days * impact
    return round(income_loss, 2)


async def forecast_weekly_income(worker_id: str) -> Dict:
    """
    Forecast next 7 days of expected parcel assignments and income.
    Uses historical delivery patterns + current risk factors.
    All calculations are deterministic within the same day.
    """
    from app.models.database import get_db
    db = get_db()

    worker = await db["users"].find_one({"id": worker_id}) if db is not None else None
    avg_parcels = worker.get("avg_daily_parcels", 30) if worker else 30
    avg_income = worker.get("avg_daily_income", 500) if worker else 500

    # Get current risk level
    from app.ai.risk_engine import compute_composite_risk
    warehouse_id = worker.get("warehouse_id", "") if worker else ""
    city = worker.get("city", "") if worker else ""
    risk = await compute_composite_risk(warehouse_id, city, avg_parcels)
    risk_score = risk["composite_risk"]

    date_seed = _date_seed()
    daily_forecast = []
    total_predicted_income = 0
    total_normal_income = 0

    for day_offset in range(1, 8):
        future_date = datetime.utcnow() + timedelta(days=day_offset)
        day_of_week = future_date.weekday()

        # Weekend adjustment
        weekend_factor = 0.6 if day_of_week >= 5 else 1.0
        
        # Risk-based reduction (deterministic)
        risk_seed = f"{date_seed}:{worker_id}:forecast:{day_offset}"
        risk_variation = _seeded_value(risk_seed, 0.5, 1.0)
        risk_reduction = 1.0 - (risk_score * risk_variation)
        
        # Deterministic noise instead of random
        noise_seed = f"{date_seed}:{worker_id}:noise:{day_offset}"
        noise = _seeded_value(noise_seed, 0.85, 1.15)

        predicted_parcels = max(0, int(avg_parcels * weekend_factor * risk_reduction * noise))
        normal_parcels = max(0, int(avg_parcels * weekend_factor * noise))
        predicted_income = round(predicted_parcels * (avg_income / max(avg_parcels, 1)), 2)
        normal_income = round(normal_parcels * (avg_income / max(avg_parcels, 1)), 2)

        daily_forecast.append({
            "date": future_date.strftime("%Y-%m-%d"),
            "day": future_date.strftime("%A"),
            "predicted_parcels": predicted_parcels,
            "normal_parcels": normal_parcels,
            "predicted_income": predicted_income,
            "normal_income": normal_income,
        })

        total_predicted_income += predicted_income
        total_normal_income += normal_income

    income_loss = max(0, total_normal_income - total_predicted_income)

    return {
        "worker_id": worker_id,
        "forecast": daily_forecast,
        "summary": {
            "predicted_weekly_income": round(total_predicted_income, 2),
            "normal_weekly_income": round(total_normal_income, 2),
            "estimated_loss": round(income_loss, 2),
            "loss_percentage": round((income_loss / max(total_normal_income, 1)) * 100, 1),
            "risk_level": risk["risk_level"],
            "risk_score": risk_score,
        },
        "computed_at": datetime.utcnow().isoformat(),
    }
