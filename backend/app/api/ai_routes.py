"""
ShieldPay AI — AI Intelligence Routes
========================================
Merges the AI pipeline ML models directly into the main backend.
Provides real-time risk, fraud, trust, premium, disruption, and simulation endpoints.
"""

import numpy as np
import joblib
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from contextlib import asynccontextmanager

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# ─── Paths ──────────────────────────────────────────────────
AI_PIPELINE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "ai_pipeline"
MODELS_DIR = AI_PIPELINE_DIR / "models" / "saved"

# Ensure ai_pipeline is importable
if str(AI_PIPELINE_DIR.parent) not in sys.path:
    sys.path.insert(0, str(AI_PIPELINE_DIR.parent))

router = APIRouter()

# ─── Global model store ────────────────────────────────────
ai_models = {}

# ─── In-memory data stores ─────────────────────────────────
financial_history = []
disruption_events = []
claim_decisions = []
fraud_alerts_store = []


def load_ai_models():
    """Load all ML models at startup."""
    model_files = {
        "risk_model": MODELS_DIR / "risk_xgb.pkl",
        "income_loss_model": MODELS_DIR / "income_loss_model.pkl",
        "fraud_model": MODELS_DIR / "fraud_iforest.pkl",
        "feature_scaler": MODELS_DIR / "feature_scaler.pkl",
        "fraud_scaler": MODELS_DIR / "fraud_scaler.pkl",
    }

    for name, path in model_files.items():
        if path.exists():
            ai_models[name] = joblib.load(path)
            print(f"  ✅ AI Model loaded: {name}")
        else:
            print(f"  ⚠ AI Model not found: {name} at {path}")

    # Seed initial financial data
    _seed_financial_data()
    # Seed initial disruption events
    _seed_disruption_events()

    print(f"  📦 {len(ai_models)} AI models loaded")


def _seed_financial_data():
    """Generate initial weekly financial trend data."""
    global financial_history
    rng = np.random.default_rng(42)
    now = datetime.utcnow()
    financial_history = []
    for i in range(8):
        week_start = now - timedelta(weeks=7 - i)
        premiums = round(float(rng.uniform(8000, 18000)), 2)
        payouts = round(float(rng.uniform(2000, premiums * 0.7)), 2)
        financial_history.append({
            "week": f"W{i + 1}",
            "week_start": week_start.strftime("%Y-%m-%d"),
            "premiums": premiums,
            "payouts": payouts,
            "net": round(premiums - payouts, 2),
            "claims_count": int(rng.integers(5, 25)),
        })


def _seed_disruption_events():
    """Generate initial disruption events from weather simulation."""
    global disruption_events
    disruption_events = _simulate_weather_feed()


# ─── City Weather Profiles ─────────────────────────────────

CITY_WEATHER_PROFILES = {
    "Mumbai": {"rain_base": 85, "flood_prob": 0.40, "traffic_base": 0.80, "risk_index": 0.75},
    "Delhi": {"rain_base": 25, "flood_prob": 0.10, "traffic_base": 0.75, "risk_index": 0.45},
    "Bangalore": {"rain_base": 55, "flood_prob": 0.15, "traffic_base": 0.85, "risk_index": 0.55},
    "Chennai": {"rain_base": 70, "flood_prob": 0.35, "traffic_base": 0.65, "risk_index": 0.70},
    "Kolkata": {"rain_base": 75, "flood_prob": 0.30, "traffic_base": 0.70, "risk_index": 0.65},
    "Pune": {"rain_base": 40, "flood_prob": 0.12, "traffic_base": 0.55, "risk_index": 0.35},
    "Hyderabad": {"rain_base": 45, "flood_prob": 0.18, "traffic_base": 0.60, "risk_index": 0.40},
    "Ahmedabad": {"rain_base": 15, "flood_prob": 0.08, "traffic_base": 0.50, "risk_index": 0.30},
}

WAREHOUSE_REGISTRY = [
    {"id": "WH-001", "city": "Mumbai", "zone": "ZONE-MUM-1", "capacity": 5000},
    {"id": "WH-002", "city": "Delhi", "zone": "ZONE-DEL-1", "capacity": 4500},
    {"id": "WH-003", "city": "Bangalore", "zone": "ZONE-BAN-1", "capacity": 3500},
    {"id": "WH-004", "city": "Chennai", "zone": "ZONE-CHE-1", "capacity": 4000},
    {"id": "WH-005", "city": "Pune", "zone": "ZONE-PUN-1", "capacity": 2500},
    {"id": "WH-006", "city": "Kolkata", "zone": "ZONE-KOL-1", "capacity": 3000},
    {"id": "WH-007", "city": "Hyderabad", "zone": "ZONE-HYD-1", "capacity": 3200},
    {"id": "WH-008", "city": "Ahmedabad", "zone": "ZONE-AHM-1", "capacity": 2000},
]


# ─── Feature Engineering ───────────────────────────────────

def _engineer_features(data: dict) -> np.ndarray:
    """Compute derived features from raw input and return full feature vector."""
    rain_norm = data["rainfall_last_3day_avg"] / 350.0

    disruption_risk = min(1.0,
        rain_norm * 0.35 +
        data["flood_zone_flag"] * 0.25 +
        data["traffic_peak_index"] * 0.25 +
        data["pollution_spike_flag"] * 0.15
    )

    gps_stability = max(0, 1.0 - data["gps_jump_distance"] / 80.0)
    mobility_stability = min(1.0, gps_stability * 0.6 + data["active_hours_ratio"] * 0.4)

    demand_dev = abs(data["parcel_demand_index"] - 0.65)
    logistics_vol = min(1.0, demand_dev * 1.2 + data["historical_income_variance"] * 0.5)

    claim_norm = min(1.0, data["claim_frequency_7day"] / 10.0)
    behavioral_trust = min(1.0,
        data["active_hours_ratio"] * 0.35 +
        (1.0 - claim_norm) * 0.35 +
        (1.0 - data["nearby_claim_cluster_score"]) * 0.30
    )

    rain_traffic = rain_norm * data["traffic_peak_index"]
    flood_claim = data["flood_zone_flag"] * claim_norm
    gps_claim = min(1.0, data["gps_jump_distance"] / 80.0) * claim_norm

    feature_vector = [
        data["city_risk_index"],
        data["rainfall_last_3day_avg"],
        data["flood_zone_flag"],
        data["traffic_peak_index"],
        data["pollution_spike_flag"],
        data["parcel_demand_index"],
        data["historical_income_variance"],
        data["active_hours_ratio"],
        data["gps_jump_distance"],
        data["claim_frequency_7day"],
        data["nearby_claim_cluster_score"],
        disruption_risk,
        mobility_stability,
        logistics_vol,
        behavioral_trust,
        rain_traffic,
        flood_claim,
        gps_claim,
    ]

    return np.array(feature_vector).reshape(1, -1), {
        "disruption_risk": round(float(disruption_risk), 4),
        "mobility_stability": round(float(mobility_stability), 4),
        "logistics_volatility": round(float(logistics_vol), 4),
        "behavioral_trust": round(float(behavioral_trust), 4),
    }


# ─── Weather Simulation ────────────────────────────────────

def _simulate_weather_feed(override_city=None, override_type=None) -> list:
    """Simulate real-time weather disruption data for all cities."""
    rng = np.random.default_rng(int(datetime.utcnow().timestamp()) % 2**31)
    events = []

    for city, profile in CITY_WEATHER_PROFILES.items():
        rainfall = max(0, profile["rain_base"] + rng.normal(0, 30))
        traffic = min(1.0, max(0.1, profile["traffic_base"] + rng.normal(0, 0.1)))

        # Apply overrides for specific simulation scenarios
        if override_city and override_city.lower() == city.lower():
            if override_type == "heavy_rain":
                rainfall = max(rainfall, 150 + rng.normal(0, 20))
                traffic = min(1.0, traffic + 0.2)
            elif override_type == "warehouse_shutdown":
                traffic = min(1.0, traffic + 0.15)

        flood_prob_adjusted = profile["flood_prob"] + (0.2 if rainfall > 100 else 0)
        is_flood = rng.random() < flood_prob_adjusted
        pollution = rng.random() < (0.5 if rainfall < 20 and traffic > 0.7 else 0.15)

        severity = 0.0
        if rainfall > 80:
            severity += 0.3
        if is_flood:
            severity += 0.35
        if traffic > 0.85:
            severity += 0.15
        severity = min(1.0, severity)

        # Determine disruption type
        if rainfall > 100 or is_flood:
            dtype = "weather"
            description = f"{'Flooding' if is_flood else 'Heavy Rain'} in {city}"
            weather_data = {"condition": "flooding" if is_flood else "heavy_rain", "rainfall_mm": round(float(rainfall), 1)}
            traffic_data = None
        elif traffic > 0.85:
            dtype = "traffic_gridlock"
            description = f"Severe traffic gridlock near {city} Hub"
            weather_data = None
            traffic_data = {"congestion_index": round(float(traffic), 3)}
        else:
            dtype = "weather"
            description = f"{'Moderate Rain' if rainfall > 40 else 'Light conditions'} in {city}"
            weather_data = {"condition": "moderate_rain" if rainfall > 40 else "clear", "rainfall_mm": round(float(rainfall), 1)}
            traffic_data = None

        event = {
            "id": len(events) + 1,
            "type": dtype,
            "description": description,
            "severity": round(float(severity), 3),
            "zone": f"ZONE-{city[:3].upper()}-1",
            "city": city,
            "is_active": severity > 0.3,
            "detected_at": datetime.utcnow().isoformat(),
            "rainfall_mm": round(float(rainfall), 1),
            "flood_zone_active": bool(is_flood),
            "traffic_index": round(float(traffic), 3),
            "pollution_spike": bool(pollution),
            "weather_data": weather_data,
            "traffic_data": traffic_data,
        }
        events.append(event)

    return events


# ─── Request / Response Schemas ─────────────────────────────

class RiskPredictionRequest(BaseModel):
    city_risk_index: float = Field(0.5, ge=0, le=1)
    rainfall_last_3day_avg: float = Field(50.0, ge=0)
    flood_zone_flag: int = Field(0, ge=0, le=1)
    traffic_peak_index: float = Field(0.5, ge=0, le=1)
    pollution_spike_flag: int = Field(0, ge=0, le=1)
    parcel_demand_index: float = Field(0.5, ge=0, le=1)
    historical_income_variance: float = Field(0.3, ge=0, le=1)
    active_hours_ratio: float = Field(0.7, ge=0, le=1)
    gps_jump_distance: float = Field(5.0, ge=0)
    claim_frequency_7day: float = Field(1.0, ge=0)
    nearby_claim_cluster_score: float = Field(0.2, ge=0, le=1)


class IncomeLossRequest(BaseModel):
    city_risk_index: float = Field(0.5, ge=0, le=1)
    rainfall_last_3day_avg: float = Field(50.0, ge=0)
    flood_zone_flag: int = Field(0, ge=0, le=1)
    traffic_peak_index: float = Field(0.5, ge=0, le=1)
    pollution_spike_flag: int = Field(0, ge=0, le=1)
    parcel_demand_index: float = Field(0.5, ge=0, le=1)
    historical_income_variance: float = Field(0.3, ge=0, le=1)
    active_hours_ratio: float = Field(0.7, ge=0, le=1)
    gps_jump_distance: float = Field(5.0, ge=0)
    claim_frequency_7day: float = Field(1.0, ge=0)
    nearby_claim_cluster_score: float = Field(0.2, ge=0, le=1)


class FraudDetectionRequest(BaseModel):
    gps_jump_distance: float = Field(5.0, ge=0)
    claim_frequency_7day: float = Field(1.0, ge=0)
    active_hours_ratio: float = Field(0.7, ge=0, le=1)
    nearby_claim_cluster_score: float = Field(0.2, ge=0, le=1)


class TrustScoreRequest(BaseModel):
    mobility_stability_index: float = Field(0.7, ge=0, le=1)
    behavioral_trust_index: float = Field(0.7, ge=0, le=1)
    fraud_anomaly_score: float = Field(0.2, ge=0, le=1)
    disruption_risk_score: float = Field(0.5, ge=0, le=1)


class PremiumRequest(BaseModel):
    city_risk_index: float = Field(0.5, ge=0, le=1)
    rainfall_last_3day_avg: float = Field(50.0, ge=0)
    flood_zone_flag: int = Field(0, ge=0, le=1)
    traffic_peak_index: float = Field(0.5, ge=0, le=1)
    pollution_spike_flag: int = Field(0, ge=0, le=1)
    parcel_demand_index: float = Field(0.5, ge=0, le=1)
    historical_income_variance: float = Field(0.3, ge=0, le=1)
    active_hours_ratio: float = Field(0.7, ge=0, le=1)
    gps_jump_distance: float = Field(5.0, ge=0)
    claim_frequency_7day: float = Field(1.0, ge=0)
    nearby_claim_cluster_score: float = Field(0.2, ge=0, le=1)
    coverage_amount: float = Field(2000.0, ge=500, le=10000)


class SimulationRequest(BaseModel):
    type: str = Field("heavy_rain", description="heavy_rain | warehouse_shutdown | fraud_cluster")
    city: Optional[str] = Field("Mumbai", description="Target city for simulation")


# ─── Endpoints ──────────────────────────────────────────────

@router.post("/predict-risk")
async def predict_risk(request: RiskPredictionRequest):
    """Predict income loss risk using XGBoost classifier."""
    if "risk_model" not in ai_models:
        raise HTTPException(status_code=503, detail="Risk model not loaded. Run training pipeline first.")

    model = ai_models["risk_model"]
    features, derived = _engineer_features(request.model_dump())

    prediction = model.predict(features)[0]
    probability = float(model.predict_proba(features)[0][1])

    if probability >= 0.75:
        risk_level = "critical"
    elif probability >= 0.50:
        risk_level = "high"
    elif probability >= 0.30:
        risk_level = "moderate"
    else:
        risk_level = "low"

    return {
        "risk_score": round(probability, 4),
        "risk_level": risk_level,
        "high_risk": bool(prediction),
        "derived_features": derived,
        "model_version": "xgb_v1",
    }


@router.post("/predict-income-loss")
async def predict_income_loss(request: IncomeLossRequest):
    """Predict expected income loss hours using XGBoost regressor."""
    if "income_loss_model" not in ai_models:
        raise HTTPException(status_code=503, detail="Income loss model not loaded.")

    model = ai_models["income_loss_model"]
    features, derived = _engineer_features(request.model_dump())

    predicted_hours = float(model.predict(features)[0])
    predicted_hours = max(0, round(predicted_hours, 2))

    if predicted_hours >= 20:
        severity = "critical"
    elif predicted_hours >= 12:
        severity = "high"
    elif predicted_hours >= 5:
        severity = "moderate"
    else:
        severity = "low"

    return {
        "expected_income_loss_hours": predicted_hours,
        "severity_level": severity,
        "derived_features": derived,
        "model_version": "xgb_reg_v1",
    }


@router.post("/detect-fraud")
async def detect_fraud(request: FraudDetectionRequest):
    """Detect fraudulent claim patterns using IsolationForest."""
    if "fraud_model" not in ai_models:
        raise HTTPException(status_code=503, detail="Fraud model not loaded.")
    if "fraud_scaler" not in ai_models:
        raise HTTPException(status_code=503, detail="Fraud scaler not loaded.")

    model = ai_models["fraud_model"]
    scaler = ai_models["fraud_scaler"]

    features = np.array([[
        request.gps_jump_distance,
        request.claim_frequency_7day,
        request.active_hours_ratio,
        request.nearby_claim_cluster_score,
    ]])

    features_scaled = scaler.transform(features)
    raw_score = model.decision_function(features_scaled)[0]
    prediction = model.predict(features_scaled)[0]
    anomaly_score = float(max(0, min(1, 0.5 - raw_score)))
    is_suspicious = prediction == -1

    if anomaly_score >= 0.8:
        risk_level = "critical"
    elif anomaly_score >= 0.6:
        risk_level = "high"
    elif anomaly_score >= 0.4:
        risk_level = "moderate"
    else:
        risk_level = "low"

    return {
        "fraud_anomaly_score": round(anomaly_score, 4),
        "fraud_flag": bool(is_suspicious),
        "is_suspicious": bool(is_suspicious),
        "risk_level": risk_level,
        "model_version": "iforest_v1",
    }


@router.post("/calculate-trust-score")
async def calculate_trust_score(request: TrustScoreRequest):
    """Calculate composite trust score for claim verification."""
    from ai_pipeline.trust_engine import compute_trust_score

    result = compute_trust_score(
        mobility_stability_index=request.mobility_stability_index,
        behavioral_trust_index=request.behavioral_trust_index,
        fraud_anomaly_score=request.fraud_anomaly_score,
        disruption_risk_score=request.disruption_risk_score,
    )

    # Map to payout tier
    score = result["trust_score"]
    if score >= 0.85:
        payout_tier = "instant"
    elif score >= 0.50:
        payout_tier = "soft_verify"
    else:
        payout_tier = "delayed_review"

    return {
        **result,
        "payout_tier": payout_tier,
    }


@router.post("/calculate-premium")
async def calculate_premium(request: PremiumRequest):
    """Calculate dynamic weekly premium based on risk profile."""
    data = request.model_dump()
    features, derived = _engineer_features(data)

    # Get risk probability
    risk_prob = 0.5
    if "risk_model" in ai_models:
        risk_prob = float(ai_models["risk_model"].predict_proba(features)[0][1])

    # Get income loss hours
    loss_hours = 8.0
    if "income_loss_model" in ai_models:
        loss_hours = float(ai_models["income_loss_model"].predict(features)[0])
        loss_hours = max(0, loss_hours)

    # Base price
    base_price = 25.0
    # Income volatility component
    income_volatility = round(data["historical_income_variance"] * 15, 2)
    # Risk multiplier
    risk_multiplier = round(1.0 + risk_prob * 2.0, 2)
    risk_multiplier = min(risk_multiplier, 3.0)
    # Reliability discount
    reliability_discount = round((1.0 - data.get("claim_frequency_7day", 1) / 10.0) * 5, 2)
    reliability_discount = max(0, reliability_discount)

    # Final premium
    dynamic_premium = round(
        (base_price + income_volatility) * risk_multiplier - reliability_discount,
        2
    )
    dynamic_premium = max(15.0, min(dynamic_premium, 150.0))

    return {
        "dynamic_weekly_premium": dynamic_premium,
        "risk_probability": round(risk_prob, 4),
        "predicted_loss_hours": round(loss_hours, 2),
        "breakdown": {
            "base_price": base_price,
            "income_volatility": income_volatility,
            "risk_multiplier": risk_multiplier,
            "reliability_discount": reliability_discount,
        },
        "coverage_amount": data["coverage_amount"],
        "formula": f"({base_price} + {income_volatility}) × {risk_multiplier} - {reliability_discount} = ₹{dynamic_premium}/week",
    }


@router.get("/active-disruptions")
async def get_active_disruptions():
    """Get real-time disruption events from weather/traffic simulation."""
    global disruption_events
    # Refresh events
    disruption_events = _simulate_weather_feed()
    return {
        "disruptions": disruption_events,
        "active_count": sum(1 for e in disruption_events if e["is_active"]),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/financial-trend")
async def get_financial_trend():
    """Get premium vs payout weekly time-series data."""
    total_premiums = sum(w["premiums"] for w in financial_history)
    total_payouts = sum(w["payouts"] for w in financial_history)
    return {
        "trend": financial_history,
        "summary": {
            "total_premiums": round(total_premiums, 2),
            "total_payouts": round(total_payouts, 2),
            "net_position": round(total_premiums - total_payouts, 2),
            "liquidity_ratio": round(total_premiums / max(total_payouts, 1), 3),
            "total_weeks": len(financial_history),
        }
    }


@router.get("/fraud-heatmap")
async def get_fraud_heatmap():
    """Get fraud counts aggregated by city."""
    rng = np.random.default_rng(int(datetime.utcnow().timestamp() / 300) % 2**31)  # Changes every 5 min

    heatmap = []
    for city, profile in CITY_WEATHER_PROFILES.items():
        # Simulate fraud counts correlated with city risk
        base_alerts = int(profile["risk_index"] * 30)
        alerts = max(1, base_alerts + int(rng.normal(0, 5)))
        severity = min(1.0, profile["risk_index"] + float(rng.normal(0, 0.1)))
        severity = max(0.1, severity)

        # Add stored fraud alert counts
        stored_count = sum(1 for a in fraud_alerts_store if a.get("city") == city)
        alerts += stored_count

        if severity > 0.7:
            color = "#ef4444"
        elif severity > 0.4:
            color = "#f59e0b"
        elif severity > 0.2:
            color = "#22d3ee"
        else:
            color = "#10b981"

        heatmap.append({
            "city": city,
            "alerts": alerts,
            "severity": round(severity, 3),
            "color": color,
        })

    # Sort by alerts descending
    heatmap.sort(key=lambda x: x["alerts"], reverse=True)
    return {"heatmap": heatmap}


@router.get("/warehouse-risk")
async def get_warehouse_risk():
    """Get warehouse risk predictions."""
    rng = np.random.default_rng(int(datetime.utcnow().timestamp() / 300) % 2**31)

    warehouses = []
    for wh in WAREHOUSE_REGISTRY:
        city_profile = CITY_WEATHER_PROFILES.get(wh["city"], {})
        base_risk = city_profile.get("risk_index", 0.3)

        # If we have a risk model, predict warehouse risk
        if "risk_model" in ai_models:
            features_data = {
                "city_risk_index": base_risk,
                "rainfall_last_3day_avg": float(city_profile.get("rain_base", 50) + rng.normal(0, 15)),
                "flood_zone_flag": 1 if base_risk > 0.6 else 0,
                "traffic_peak_index": city_profile.get("traffic_base", 0.5),
                "pollution_spike_flag": 0,
                "parcel_demand_index": round(float(rng.uniform(0.3, 0.8)), 4),
                "historical_income_variance": round(float(rng.uniform(0.1, 0.5)), 4),
                "active_hours_ratio": round(float(rng.uniform(0.5, 0.9)), 4),
                "gps_jump_distance": round(float(rng.exponential(3.0)), 2),
                "claim_frequency_7day": round(float(rng.poisson(2.0)), 1),
                "nearby_claim_cluster_score": round(float(rng.uniform(0.1, 0.4)), 4),
            }
            features, _ = _engineer_features(features_data)
            risk_score = float(ai_models["risk_model"].predict_proba(features)[0][1])
        else:
            risk_score = base_risk + float(rng.normal(0, 0.1))

        risk_score = max(0.05, min(0.99, risk_score))

        warehouses.append({
            "id": wh["id"],
            "city": wh["city"],
            "zone": wh["zone"],
            "risk": round(risk_score, 3),
            "capacity": wh["capacity"],
        })

    # Sort by risk descending
    warehouses.sort(key=lambda x: x["risk"], reverse=True)
    return {"warehouses": warehouses}


@router.post("/simulate-disruption")
async def simulate_disruption(request: SimulationRequest):
    """
    Trigger a disruption simulation.
    Runs the full AI pipeline: weather → risk → fraud → trust → claim generation.
    """
    global disruption_events, financial_history, claim_decisions, fraud_alerts_store

    rng = np.random.default_rng(int(datetime.utcnow().timestamp()) % 2**31)
    sim_type = request.type
    target_city = request.city or "Mumbai"

    # Step 1: Generate disruption events with overrides
    if sim_type == "fraud_cluster":
        # Fraud cluster doesn't change weather, just generates suspicious workers
        events = disruption_events
    else:
        events = _simulate_weather_feed(
            override_city=target_city,
            override_type=sim_type
        )
        disruption_events = events

    # Add warehouse shutdown event if needed
    if sim_type == "warehouse_shutdown":
        wh = next((w for w in WAREHOUSE_REGISTRY if w["city"].lower() == target_city.lower()), WAREHOUSE_REGISTRY[0])
        shutdown_event = {
            "id": len(events) + 100,
            "type": "warehouse_shutdown",
            "description": f"Warehouse {wh['id']} shutdown: power failure",
            "severity": round(float(0.7 + rng.uniform(0, 0.25)), 3),
            "zone": wh["zone"],
            "city": wh["city"],
            "is_active": True,
            "detected_at": datetime.utcnow().isoformat(),
            "rainfall_mm": 0,
            "flood_zone_active": False,
            "traffic_index": 0.7,
            "pollution_spike": False,
            "weather_data": None,
            "traffic_data": None,
        }
        disruption_events.append(shutdown_event)

    # Step 2: Process affected workers through AI pipeline
    new_claims = []
    active_events = [e for e in disruption_events if e["is_active"]]

    if sim_type == "fraud_cluster":
        # Generate fraud cluster workers
        for i in range(5):
            worker_data = {
                "city_risk_index": round(float(rng.uniform(0.1, 0.3)), 4),
                "rainfall_last_3day_avg": round(float(rng.uniform(5, 30)), 2),
                "flood_zone_flag": 0,
                "traffic_peak_index": round(float(rng.uniform(0.3, 0.5)), 4),
                "pollution_spike_flag": 0,
                "parcel_demand_index": round(float(rng.uniform(0.4, 0.9)), 4),
                "historical_income_variance": round(float(rng.uniform(0.3, 0.8)), 4),
                "active_hours_ratio": round(float(rng.uniform(0.05, 0.30)), 4),
                "gps_jump_distance": round(float(rng.uniform(15, 80)), 2),
                "claim_frequency_7day": round(float(rng.uniform(4, 10)), 1),
                "nearby_claim_cluster_score": round(float(rng.uniform(0.6, 0.95)), 4),
            }
            claim = _process_single_claim(worker_data, target_city, rng)
            new_claims.append(claim)
            # Store fraud alert
            fraud_alerts_store.append({
                "city": target_city,
                "worker": f"Worker_{rng.integers(1000, 9999)}",
                "type": rng.choice(["gps_spoof", "claim_spike", "ring_detected"]),
                "severity": claim["fraud"]["anomaly_score"],
                "details": f"Suspicious pattern: GPS jump {worker_data['gps_jump_distance']:.1f}km, {worker_data['claim_frequency_7day']:.0f} claims/7d",
                "time": datetime.utcnow().isoformat(),
            })
    else:
        # Process genuine disruption with some potential fraudsters
        for event in active_events[:3]:  # Cap at 3 events
            n_workers = int(rng.integers(2, 5))
            for w in range(n_workers):
                is_genuine = rng.random() > 0.08
                if is_genuine:
                    worker_data = {
                        "city_risk_index": round(float(event["severity"]), 4),
                        "rainfall_last_3day_avg": event["rainfall_mm"],
                        "flood_zone_flag": int(event["flood_zone_active"]),
                        "traffic_peak_index": event["traffic_index"],
                        "pollution_spike_flag": int(event["pollution_spike"]),
                        "parcel_demand_index": round(float(rng.uniform(0.3, 0.8)), 4),
                        "historical_income_variance": round(float(rng.uniform(0.1, 0.5)), 4),
                        "active_hours_ratio": round(float(rng.uniform(0.5, 0.95)), 4),
                        "gps_jump_distance": round(float(rng.exponential(2.0)), 2),
                        "claim_frequency_7day": round(float(rng.poisson(1.5)), 1),
                        "nearby_claim_cluster_score": round(float(rng.uniform(0.05, 0.35)), 4),
                    }
                else:
                    worker_data = {
                        "city_risk_index": round(float(rng.uniform(0.1, 0.3)), 4),
                        "rainfall_last_3day_avg": round(float(rng.uniform(5, 30)), 2),
                        "flood_zone_flag": 0,
                        "traffic_peak_index": round(float(rng.uniform(0.3, 0.5)), 4),
                        "pollution_spike_flag": 0,
                        "parcel_demand_index": round(float(rng.uniform(0.4, 0.9)), 4),
                        "historical_income_variance": round(float(rng.uniform(0.3, 0.8)), 4),
                        "active_hours_ratio": round(float(rng.uniform(0.05, 0.30)), 4),
                        "gps_jump_distance": round(float(rng.uniform(15, 80)), 2),
                        "claim_frequency_7day": round(float(rng.uniform(4, 10)), 1),
                        "nearby_claim_cluster_score": round(float(rng.uniform(0.6, 0.95)), 4),
                    }
                claim = _process_single_claim(worker_data, event["city"], rng)
                new_claims.append(claim)

    # Step 3: Update financial data
    if new_claims:
        week_premiums = sum(c.get("premium", 0) for c in new_claims)
        week_payouts = sum(c.get("payout", 0) for c in new_claims)
        financial_history.append({
            "week": f"W{len(financial_history) + 1}",
            "week_start": datetime.utcnow().strftime("%Y-%m-%d"),
            "premiums": round(week_premiums + float(rng.uniform(5000, 12000)), 2),
            "payouts": round(week_payouts, 2),
            "net": round(week_premiums - week_payouts + float(rng.uniform(3000, 10000)), 2),
            "claims_count": len(new_claims),
        })
        # Keep last 12 weeks
        financial_history = financial_history[-12:]

    claim_decisions.extend(new_claims)

    # Compute summary stats
    stats = {
        "total_processed": len(new_claims),
        "auto_approved": sum(1 for c in new_claims if c["decision"] == "AUTO_APPROVE"),
        "manual_review": sum(1 for c in new_claims if c["decision"] == "MANUAL_REVIEW"),
        "flagged": sum(1 for c in new_claims if c["decision"] == "FLAG_SUSPICIOUS"),
        "auto_rejected": sum(1 for c in new_claims if c["decision"] == "AUTO_REJECT"),
    }

    return {
        "simulation_type": sim_type,
        "target_city": target_city,
        "claims": new_claims,
        "stats": stats,
        "disruption_events": len([e for e in disruption_events if e["is_active"]]),
        "timestamp": datetime.utcnow().isoformat(),
    }


def _process_single_claim(worker_data: dict, city: str, rng) -> dict:
    """Run the full AI pipeline on a single worker's data."""
    features, derived = _engineer_features(worker_data)

    result = {
        "id": f"CLM-{rng.integers(10000, 99999)}",
        "city": city,
        "timestamp": datetime.utcnow().isoformat(),
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
    }

    # Risk prediction
    if "risk_model" in ai_models:
        risk_prob = float(ai_models["risk_model"].predict_proba(features)[0][1])
        result["risk"] = {
            "probability": round(risk_prob, 4),
            "high_risk": risk_prob > 0.5,
            "level": "critical" if risk_prob >= 0.75 else "high" if risk_prob >= 0.5 else "moderate" if risk_prob >= 0.3 else "low",
        }
    else:
        risk_prob = derived["disruption_risk"]
        result["risk"] = {"probability": risk_prob, "high_risk": risk_prob > 0.5, "level": "moderate"}

    # Income loss prediction
    if "income_loss_model" in ai_models:
        loss_hours = float(ai_models["income_loss_model"].predict(features)[0])
        loss_hours = max(0, round(loss_hours, 2))
        result["income_loss"] = {"expected_hours": loss_hours}
    else:
        loss_hours = 8.0
        result["income_loss"] = {"expected_hours": loss_hours}

    # Fraud detection
    anomaly_score = 0.0
    if "fraud_model" in ai_models and "fraud_scaler" in ai_models:
        fraud_features = np.array([[
            worker_data["gps_jump_distance"],
            worker_data["claim_frequency_7day"],
            worker_data["active_hours_ratio"],
            worker_data["nearby_claim_cluster_score"],
        ]])
        fraud_scaled = ai_models["fraud_scaler"].transform(fraud_features)
        fraud_raw = ai_models["fraud_model"].decision_function(fraud_scaled)[0]
        fraud_pred = ai_models["fraud_model"].predict(fraud_scaled)[0]
        anomaly_score = float(max(0, min(1, 0.5 - fraud_raw)))
        result["fraud"] = {
            "anomaly_score": round(anomaly_score, 4),
            "is_suspicious": bool(fraud_pred == -1),
        }
    else:
        result["fraud"] = {"anomaly_score": 0.0, "is_suspicious": False}

    # Trust score
    from ai_pipeline.trust_engine import compute_trust_score
    trust_result = compute_trust_score(
        mobility_stability_index=derived["mobility_stability"],
        behavioral_trust_index=derived["behavioral_trust"],
        fraud_anomaly_score=anomaly_score,
        disruption_risk_score=derived["disruption_risk"],
    )
    result["trust"] = trust_result["trust_score"]
    result["decision"] = trust_result["recommendation"]
    result["explanation"] = trust_result["explanation"]

    # Payout tier
    if trust_result["trust_score"] >= 0.85:
        result["tier"] = "instant"
        payout_rate = 1.0
    elif trust_result["trust_score"] >= 0.50:
        result["tier"] = "soft_verify"
        payout_rate = 0.7
    else:
        result["tier"] = "delayed"
        payout_rate = 0.0

    # Compute payout (based on loss hours and hourly rate)
    hourly_rate = 150  # ₹150/hour
    result["payout"] = round(loss_hours * hourly_rate * payout_rate, 2)
    result["premium"] = round(25 + risk_prob * 20, 2)

    # Map decision → status
    decision_map = {
        "AUTO_APPROVE": "auto_approved",
        "MANUAL_REVIEW": "soft_verify",
        "FLAG_SUSPICIOUS": "delayed_review",
        "AUTO_REJECT": "rejected",
    }
    result["status"] = decision_map.get(trust_result["recommendation"], "pending")

    # Disruption trigger text
    if worker_data.get("flood_zone_flag"):
        result["trigger"] = f"Flooding — {city}"
        result["type"] = "weather"
    elif worker_data.get("rainfall_last_3day_avg", 0) > 80:
        result["trigger"] = f"Heavy Rain — {city}"
        result["type"] = "weather"
    elif worker_data.get("gps_jump_distance", 0) > 15:
        result["trigger"] = f"Suspicious Activity — {city}"
        result["type"] = "fraud_flag"
    else:
        result["trigger"] = f"Disruption Event — {city}"
        result["type"] = "weather"

    return result


@router.get("/recent-claims")
async def get_recent_claims():
    """Get all claims generated by simulation."""
    return {
        "claims": claim_decisions[-50:],  # Last 50 claims
        "total": len(claim_decisions),
    }


@router.get("/fraud-alerts")
async def get_fraud_alerts_ai():
    """Get AI-generated fraud alerts."""
    return {
        "alerts": fraud_alerts_store[-20:],
        "total": len(fraud_alerts_store),
    }
