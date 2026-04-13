"""
ShieldPay AI — Logistics Disruption Risk Intelligence Engine
Predicts probability of delivery allocation loss using:
  • warehouse geospatial risk
  • historical parcel demand volatility  
  • weather severity forecasting
  • traffic congestion index
  • seasonal logistics cycles

All risk factors use deterministic, date-seeded variation
for consistent results within the same day.
"""
import hashlib
from datetime import datetime
from typing import Dict


# ─── Deterministic Seeded Value ───────────────────────────

def _seeded_value(seed_str: str, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Generate a deterministic float from a seed string."""
    h = int(hashlib.sha256(seed_str.encode()).hexdigest()[:8], 16)
    normalized = (h % 10000) / 10000.0
    return min_val + normalized * (max_val - min_val)


def _date_seed() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


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

# Base risk profiles per city (with daily variation applied on top)
CITY_WEATHER_PROFILES = {
    "Mumbai":    {"base": 0.75, "condition": "heavy_rain", "rainfall_mm": 120},
    "Delhi":     {"base": 0.50, "condition": "extreme_heat", "rainfall_mm": 0},
    "Bangalore": {"base": 0.30, "condition": "moderate_rain", "rainfall_mm": 40},
    "Hyderabad": {"base": 0.20, "condition": "partly_cloudy", "rainfall_mm": 5},
    "Chennai":   {"base": 0.85, "condition": "cyclone_warning", "rainfall_mm": 180},
    "Pune":      {"base": 0.15, "condition": "clear", "rainfall_mm": 0},
    "Kolkata":   {"base": 0.80, "condition": "flooding", "rainfall_mm": 200},
    "Ahmedabad": {"base": 0.40, "condition": "heatwave", "rainfall_mm": 0},
}

CITY_TRAFFIC_PROFILES = {
    "Mumbai":    {"base": 0.80, "congestion_index": 0.85, "avg_speed_kmh": 12},
    "Delhi":     {"base": 0.75, "congestion_index": 0.80, "avg_speed_kmh": 15},
    "Bangalore": {"base": 0.90, "congestion_index": 0.92, "avg_speed_kmh": 8},
    "Hyderabad": {"base": 0.50, "congestion_index": 0.55, "avg_speed_kmh": 25},
    "Chennai":   {"base": 0.65, "congestion_index": 0.70, "avg_speed_kmh": 18},
    "Pune":      {"base": 0.55, "congestion_index": 0.60, "avg_speed_kmh": 22},
    "Kolkata":   {"base": 0.70, "congestion_index": 0.75, "avg_speed_kmh": 16},
    "Ahmedabad": {"base": 0.45, "congestion_index": 0.50, "avg_speed_kmh": 28},
}


async def get_weather_risk(city: str) -> Dict:
    """Get weather-based disruption risk with daily deterministic variation."""
    date_seed = _date_seed()
    profile = CITY_WEATHER_PROFILES.get(city)
    
    if profile:
        # Apply daily variation (±15%) to the base score
        variation = _seeded_value(f"{date_seed}:weather:{city}", -0.15, 0.15)
        score = max(0.0, min(1.0, profile["base"] + variation))
        
        # Adjust rainfall proportionally
        rainfall_var = _seeded_value(f"{date_seed}:rain:{city}", 0.8, 1.2)
        rainfall = int(profile["rainfall_mm"] * rainfall_var)
        
        return {
            "score": round(score, 3),
            "condition": profile["condition"],
            "rainfall_mm": rainfall,
        }
    
    # Unknown city: generate deterministic values
    score = _seeded_value(f"{date_seed}:weather:{city}", 0.1, 0.5)
    return {"score": round(score, 3), "condition": "unknown", "rainfall_mm": 0}


async def get_traffic_risk(city: str) -> Dict:
    """Get traffic congestion risk with daily deterministic variation."""
    date_seed = _date_seed()
    profile = CITY_TRAFFIC_PROFILES.get(city)
    
    if profile:
        variation = _seeded_value(f"{date_seed}:traffic:{city}", -0.1, 0.1)
        score = max(0.0, min(1.0, profile["base"] + variation))
        
        speed_var = _seeded_value(f"{date_seed}:speed:{city}", 0.85, 1.15)
        avg_speed = int(profile["avg_speed_kmh"] * speed_var)
        
        return {
            "score": round(score, 3),
            "congestion_index": round(profile["congestion_index"] + variation, 3),
            "avg_speed_kmh": avg_speed,
        }
    
    score = _seeded_value(f"{date_seed}:traffic:{city}", 0.3, 0.7)
    return {"score": round(score, 3), "congestion_index": 0.5, "avg_speed_kmh": 20}


async def get_warehouse_risk(warehouse_id: str) -> Dict:
    """Get warehouse-specific operational risk."""
    from app.models.database import get_db
    db = get_db()

    disruptions = 0
    historical = 0

    if db is not None:
        disruptions = await db['disruption_triggers'].count_documents({
            "affected_warehouse_ids": warehouse_id,
            "is_active": True
        })
        historical = await db['disruption_triggers'].count_documents({
            "affected_warehouse_ids": warehouse_id
        })
        score = min(1.0, (disruptions * 0.3) + (historical * 0.02))
    else:
        date_seed = _date_seed()
        score = _seeded_value(f"{date_seed}:warehouse:{warehouse_id}", 0.1, 0.6)

    return {
        "score": round(score, 3),
        "active_disruptions": disruptions,
        "historical_incidents": historical,
    }


def get_seasonal_risk() -> Dict:
    """Get current seasonal risk based on Indian weather patterns."""
    month = datetime.utcnow().month
    score = SEASONAL_RISK.get(month, 0.3)
    season_name = _get_season(month)
    return {"score": score, "season": season_name, "month": month}


def get_demand_volatility(avg_daily_parcels: float) -> Dict:
    """Estimate parcel demand volatility risk."""
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
