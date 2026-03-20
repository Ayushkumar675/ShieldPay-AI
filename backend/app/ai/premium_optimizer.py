"""
ShieldPay AI — Dynamic Weekly Premium Optimizer
premium = base_price + (predicted_income_volatility × risk_multiplier)
"""
from datetime import datetime
from typing import Dict

from app.core.config import settings
from app.ai.risk_engine import compute_composite_risk


async def calculate_premium(worker: dict) -> Dict:
    """
    Calculate dynamic weekly premium for a worker.
    
    Formula: premium = base_price + (predicted_income_volatility × risk_multiplier)
    
    Factors:
    - Base price: ₹15-50 based on coverage tier
    - Risk multiplier: composite risk score from Risk Intelligence Engine
    - Income volatility: based on worker's delivery history variance
    - Reliability discount: lower premium for trusted workers
    """
    warehouse_id = worker.get("warehouse_id", "")
    city = worker.get("city", "")
    avg_parcels = worker.get("avg_daily_parcels", 30)
    avg_income = worker.get("avg_daily_income", 500)
    reliability = worker.get("reliability_score", 1.0)

    # Step 1: Get composite risk score
    risk_data = await compute_composite_risk(warehouse_id, city, avg_parcels)
    risk_score = risk_data["composite_risk"]

    # Step 2: Calculate base price (scaled by income level)
    income_factor = min(1.0, avg_income / 1000)  # normalized
    base_price = settings.BASE_PREMIUM_MIN + (
        (settings.BASE_PREMIUM_MAX - settings.BASE_PREMIUM_MIN) * income_factor
    )

    # Step 3: Income volatility estimation
    # Higher parcels = more exposure = higher volatility premium
    income_volatility = (avg_parcels / 60) * avg_income * 0.01  # ~1% of potential income

    # Step 4: Risk multiplier (capped)
    risk_multiplier = min(settings.RISK_MULTIPLIER_CAP, 1.0 + (risk_score * 2.5))

    # Step 5: Reliability discount (up to 20% off for trusted workers)
    reliability_discount = 1.0 - (reliability * 0.20)

    # Final premium calculation
    raw_premium = base_price + (income_volatility * risk_multiplier)
    final_premium = round(raw_premium * reliability_discount, 2)

    # Enforce bounds
    final_premium = max(settings.BASE_PREMIUM_MIN, min(final_premium * 2, final_premium))

    return {
        "premium": final_premium,
        "risk_score": risk_score,
        "risk_level": risk_data["risk_level"],
        "breakdown": {
            "base_price": round(base_price, 2),
            "income_volatility": round(income_volatility, 2),
            "risk_multiplier": round(risk_multiplier, 3),
            "reliability_discount": f"{round((1 - reliability_discount) * 100, 1)}%",
            "raw_premium": round(raw_premium, 2),
        },
        "formula": "premium = (base_price + income_volatility × risk_multiplier) × reliability_discount",
        "computed_at": datetime.utcnow().isoformat(),
    }
