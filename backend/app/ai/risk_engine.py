"""
ShieldPay AI — Logistics Disruption Risk Intelligence Engine
Predicts probability of delivery allocation loss using:
  • warehouse geospatial risk
  • historical parcel demand volatility  
  • weather severity forecasting
  • traffic congestion index
  • seasonal logistics cycles
"""
import random
from datetime import datetime
from typing import Dict, Optional


# ─── Risk Factor Weights ──────────────────────────────────

WEIGHTS = {
    "weather": 0.30,
    "traffic": 0.20,
    "warehouse": 0.25,
    "seasonal": 0.15,
    "demand_volatility": 0.10,
}

# Seasonal risk profiles for India (month → risk multiplier)
SEASONAL_RISK = {
    1: 0.3,   # Jan - post holiday, moderate
    2: 0.2,   # Feb - stable
    3: 0.2,   # Mar - stable
    4: 0.3,   # Apr - pre-summer
    5: 0.4,   # May - extreme heat
    6: 0.7,   # Jun - monsoon begins
    7: 0.9,   # Jul - peak monsoon
    8: 0.85,  # Aug - monsoon continues
    9: 0.6,   # Sep - monsoon retreat
    10: 0.5,  # Oct - festivals, high demand
    11: 0.3,  # Nov - stable, Diwali rush
    12: 0.25, # Dec - winter, year-end sales
}


async def get_weather_risk(city: str) -> Dict:
    """Get weather-based disruption risk for a city."""
    # In production: call OpenWeatherMap API
    # For MVP: use realistic mock data
    weather_risks = {
        "Mumbai": {"score": 0.75, "condition": "heavy_rain", "rainfall_mm": 120},
        "Delhi": {"score": 0.5, "condition": "extreme_heat", "rainfall_mm": 0},
        "Bangalore": {"score": 0.3, "condition": "moderate_rain", "rainfall_mm": 40},
        "Hyderabad": {"score": 0.2, "condition": "partly_cloudy", "rainfall_mm": 5},
        "Chennai": {"score": 0.85, "condition": "cyclone_warning", "rainfall_mm": 180},
        "Pune": {"score": 0.15, "condition": "clear", "rainfall_mm": 0},
        "Kolkata": {"score": 0.8, "condition": "flooding", "rainfall_mm": 200},
        "Ahmedabad": {"score": 0.4, "condition": "heatwave", "rainfall_mm": 0},
    }
    return weather_risks.get(city, {"score": round(random.uniform(0.1, 0.5), 2), "condition": "unknown", "rainfall_mm": 0})


async def get_traffic_risk(city: str) -> Dict:
    """Get traffic congestion risk."""
    traffic_risks = {
        "Mumbai": {"score": 0.8, "congestion_index": 0.85, "avg_speed_kmh": 12},
        "Delhi": {"score": 0.75, "congestion_index": 0.80, "avg_speed_kmh": 15},
        "Bangalore": {"score": 0.9, "congestion_index": 0.92, "avg_speed_kmh": 8},
        "Hyderabad": {"score": 0.5, "congestion_index": 0.55, "avg_speed_kmh": 25},
        "Chennai": {"score": 0.65, "congestion_index": 0.70, "avg_speed_kmh": 18},
        "Pune": {"score": 0.55, "congestion_index": 0.60, "avg_speed_kmh": 22},
        "Kolkata": {"score": 0.7, "congestion_index": 0.75, "avg_speed_kmh": 16},
        "Ahmedabad": {"score": 0.45, "congestion_index": 0.50, "avg_speed_kmh": 28},
    }
    return traffic_risks.get(city, {"score": round(random.uniform(0.3, 0.7), 2), "congestion_index": 0.5, "avg_speed_kmh": 20})


async def get_warehouse_risk(warehouse_id: str) -> Dict:
    """Get warehouse-specific operational risk."""
    from app.models.database import get_db
    db = get_db()

    # Check for recent disruptions at this warehouse
    if db:
        disruptions = await db.disruption_triggers.count_documents({
            "affected_warehouse_ids": warehouse_id,
            "is_active": True
        })
        historical = await db.disruption_triggers.count_documents({
            "affected_warehouse_ids": warehouse_id
        })
        score = min(1.0, (disruptions * 0.3) + (historical * 0.02))
    else:
        score = round(random.uniform(0.1, 0.6), 2)

    return {
        "score": round(score, 3),
        "active_disruptions": disruptions if db else 0,
        "historical_incidents": historical if db else 0,
    }


def get_seasonal_risk() -> Dict:
    """Get current seasonal risk based on Indian weather patterns."""
    month = datetime.utcnow().month
    score = SEASONAL_RISK.get(month, 0.3)
    season_name = _get_season(month)
    return {"score": score, "season": season_name, "month": month}


def get_demand_volatility(avg_daily_parcels: float) -> Dict:
    """Estimate parcel demand volatility risk."""
    # Higher volume = more dependent on stable logistics = higher risk impact
    if avg_daily_parcels > 50:
        score = 0.7
    elif avg_daily_parcels > 30:
        score = 0.5
    else:
        score = 0.3
    return {"score": score, "avg_daily_parcels": avg_daily_parcels}


async def compute_composite_risk(
    warehouse_id: str,
    city: str = "",
    avg_daily_parcels: float = 30
) -> Dict:
    """
    Compute composite logistics disruption risk score.
    Returns 0-1 score and breakdown of all risk factors.
    """
    weather = await get_weather_risk(city)
    traffic = await get_traffic_risk(city)
    warehouse = await get_warehouse_risk(warehouse_id)
    seasonal = get_seasonal_risk()
    demand = get_demand_volatility(avg_daily_parcels)

    composite = (
        weather["score"] * WEIGHTS["weather"] +
        traffic["score"] * WEIGHTS["traffic"] +
        warehouse["score"] * WEIGHTS["warehouse"] +
        seasonal["score"] * WEIGHTS["seasonal"] +
        demand["score"] * WEIGHTS["demand_volatility"]
    )

    return {
        "composite_risk": round(min(1.0, composite), 4),
        "risk_level": _risk_label(composite),
        "factors": {
            "weather": {**weather, "weight": WEIGHTS["weather"]},
            "traffic": {**traffic, "weight": WEIGHTS["traffic"]},
            "warehouse": {**warehouse, "weight": WEIGHTS["warehouse"]},
            "seasonal": {**seasonal, "weight": WEIGHTS["seasonal"]},
            "demand_volatility": {**demand, "weight": WEIGHTS["demand_volatility"]},
        },
        "computed_at": datetime.utcnow().isoformat(),
    }


async def get_risk_factors(warehouse_id: str, location: dict) -> Dict:
    """Public API for premium endpoint to get risk breakdown."""
    city = location.get("city", "") if location else ""
    return await compute_composite_risk(warehouse_id, city)


def _risk_label(score: float) -> str:
    if score >= 0.75:
        return "critical"
    elif score >= 0.5:
        return "high"
    elif score >= 0.3:
        return "moderate"
    else:
        return "low"


def _get_season(month: int) -> str:
    if month in [6, 7, 8, 9]:
        return "monsoon"
    elif month in [10, 11]:
        return "post_monsoon_festival"
    elif month in [12, 1, 2]:
        return "winter"
    else:
        return "summer"
