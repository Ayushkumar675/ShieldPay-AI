"""
ShieldPay AI — External Integrations API
Weather, traffic, and logistics disruption data APIs.
Uses mock data for demo with real API integration hooks.
"""
from fastapi import APIRouter, Depends
import random
from datetime import datetime

from app.core.auth import get_current_user, require_admin

router = APIRouter()

# ─── Mock Weather Data ────────────────────────────────────

MOCK_WEATHER_CONDITIONS = {
    "Mumbai": {"temp": 32, "humidity": 85, "condition": "heavy_rain", "rainfall_mm": 120, "wind_kmh": 45, "severity": 0.8},
    "Delhi": {"temp": 42, "humidity": 30, "condition": "extreme_heat", "rainfall_mm": 0, "wind_kmh": 15, "severity": 0.6},
    "Bangalore": {"temp": 28, "humidity": 70, "condition": "moderate_rain", "rainfall_mm": 40, "wind_kmh": 20, "severity": 0.3},
    "Hyderabad": {"temp": 35, "humidity": 55, "condition": "partly_cloudy", "rainfall_mm": 5, "wind_kmh": 12, "severity": 0.1},
    "Chennai": {"temp": 34, "humidity": 80, "condition": "cyclone_warning", "rainfall_mm": 180, "wind_kmh": 90, "severity": 0.95},
    "Pune": {"temp": 30, "humidity": 65, "condition": "clear", "rainfall_mm": 0, "wind_kmh": 8, "severity": 0.05},
    "Kolkata": {"temp": 33, "humidity": 88, "condition": "flooding", "rainfall_mm": 200, "wind_kmh": 35, "severity": 0.9},
    "Ahmedabad": {"temp": 40, "humidity": 25, "condition": "heatwave", "rainfall_mm": 0, "wind_kmh": 20, "severity": 0.5},
}


@router.get("/weather/{city}")
async def get_weather(city: str, current_user: dict = Depends(get_current_user)):
    """Get weather data for a city (mock + real API hook)."""
    city_key = city.title()
    if city_key in MOCK_WEATHER_CONDITIONS:
        data = MOCK_WEATHER_CONDITIONS[city_key].copy()
    else:
        data = {
            "temp": random.randint(20, 45),
            "humidity": random.randint(20, 95),
            "condition": random.choice(["clear", "moderate_rain", "heavy_rain"]),
            "rainfall_mm": random.randint(0, 100),
            "wind_kmh": random.randint(5, 60),
            "severity": round(random.uniform(0, 1), 2),
        }

    data["city"] = city_key
    data["timestamp"] = datetime.utcnow().isoformat()
    data["source"] = "mock_api"
    return {"weather": data}


# ─── Mock Traffic Data ────────────────────────────────────

@router.get("/traffic/{city}")
async def get_traffic(city: str, current_user: dict = Depends(get_current_user)):
    """Get traffic congestion data for a city."""
    congestion = round(random.uniform(0.1, 1.0), 2)
    return {
        "traffic": {
            "city": city.title(),
            "congestion_index": congestion,
            "avg_speed_kmh": round(max(5, 40 * (1 - congestion)), 1),
            "delays_minutes": round(congestion * 45, 1),
            "blocked_routes": random.randint(0, 5) if congestion > 0.7 else 0,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "mock_api",
        }
    }


# ─── Mock Logistics Data ─────────────────────────────────

@router.get("/logistics/{warehouse_id}")
async def get_logistics_status(warehouse_id: str, current_user: dict = Depends(get_current_user)):
    """Get logistics/warehouse operational status."""
    is_disrupted = random.random() < 0.2  # 20% chance of disruption
    return {
        "logistics": {
            "warehouse_id": warehouse_id,
            "operational": not is_disrupted,
            "dispatch_capacity_pct": random.randint(10, 40) if is_disrupted else random.randint(70, 100),
            "parcels_in_queue": random.randint(100, 5000),
            "estimated_delay_hours": random.randint(2, 24) if is_disrupted else 0,
            "disruption_reason": random.choice([
                "power_failure", "flooding", "labor_shortage", "equipment_breakdown"
            ]) if is_disrupted else None,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "mock_api",
        }
    }


@router.get("/disruptions/active")
async def get_active_disruptions(current_user: dict = Depends(get_current_user)):
    """Get all currently active disruption events."""
    from app.models.database import get_db
    db = get_db()
    cursor = db.disruption_triggers.find(
        {"is_active": True},
        {"_id": 0}
    ).sort("detected_at", -1)
    disruptions = await cursor.to_list(length=50)
    return {"active_disruptions": disruptions, "count": len(disruptions)}
