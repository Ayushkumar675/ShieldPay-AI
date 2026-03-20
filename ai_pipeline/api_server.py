"""
ShieldPay AI — AI Inference FastAPI Server
===========================================
Production-ready API endpoints that load trained ML models
and serve real-time predictions.

Endpoints:
  POST /predict-risk          → risk classification + probability
  POST /predict-income-loss   → predicted income loss hours
  POST /detect-fraud          → fraud anomaly score + flag
  POST /calculate-trust-score → composite trust score
"""

import numpy as np
import joblib
import json
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# ─── Paths ──────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models" / "saved"
REPORTS_DIR = BASE_DIR / "reports"


# ─── Global model store ────────────────────────────────────
models = {}


def load_models():
    """Load all saved models at startup."""
    model_files = {
        "risk_model": MODELS_DIR / "risk_xgb.pkl",
        "income_loss_model": MODELS_DIR / "income_loss_model.pkl",
        "fraud_model": MODELS_DIR / "fraud_iforest.pkl",
        "feature_scaler": MODELS_DIR / "feature_scaler.pkl",
        "fraud_scaler": MODELS_DIR / "fraud_scaler.pkl",
    }
    
    for name, path in model_files.items():
        if path.exists():
            models[name] = joblib.load(path)
            print(f"  ✅ Loaded {name} from {path}")
        else:
            print(f"  ⚠ {name} not found at {path}")
    
    # Load metrics
    for metrics_file in ["risk_model_metrics.json", "income_loss_metrics.json", "fraud_model_metrics.json"]:
        metrics_path = REPORTS_DIR / metrics_file
        if metrics_path.exists():
            with open(metrics_path) as f:
                models[metrics_file.replace(".json", "")] = json.load(f)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models on startup."""
    print("\n🚀 ShieldPay AI — Loading ML Models...")
    load_models()
    print(f"  📦 {len(models)} artifacts loaded\n")
    yield
    print("🛑 ShieldPay AI — Shutting down")


# ─── FastAPI App ────────────────────────────────────────────
app = FastAPI(
    title="ShieldPay AI — ML Intelligence API",
    version="1.0.0",
    description="Real-time ML inference for parametric insurance risk, income loss, fraud detection, and trust scoring.",
    lifespan=lifespan,
)


# ─── Request/Response Schemas ──────────────────────────────

class RiskPredictionRequest(BaseModel):
    """Input features for risk prediction."""
    city_risk_index: float = Field(..., ge=0, le=1, description="City risk level 0-1")
    rainfall_last_3day_avg: float = Field(..., ge=0, description="3-day avg rainfall in mm")
    flood_zone_flag: int = Field(..., ge=0, le=1, description="1 if in flood zone")
    traffic_peak_index: float = Field(..., ge=0, le=1, description="Traffic congestion 0-1")
    pollution_spike_flag: int = Field(..., ge=0, le=1, description="1 if pollution spike")
    parcel_demand_index: float = Field(..., ge=0, le=1, description="Parcel demand level 0-1")
    historical_income_variance: float = Field(..., ge=0, le=1, description="Income variance 0-1")
    active_hours_ratio: float = Field(..., ge=0, le=1, description="Active hours 0-1")
    gps_jump_distance: float = Field(..., ge=0, description="GPS jump distance km")
    claim_frequency_7day: float = Field(..., ge=0, description="Claims in last 7 days")
    nearby_claim_cluster_score: float = Field(..., ge=0, le=1, description="Cluster score 0-1")


class RiskPredictionResponse(BaseModel):
    high_risk: bool
    risk_probability: float
    risk_level: str
    model_version: str = "xgb_v1"


class IncomeLossRequest(BaseModel):
    """Input features for income loss prediction."""
    city_risk_index: float = Field(..., ge=0, le=1)
    rainfall_last_3day_avg: float = Field(..., ge=0)
    flood_zone_flag: int = Field(..., ge=0, le=1)
    traffic_peak_index: float = Field(..., ge=0, le=1)
    pollution_spike_flag: int = Field(..., ge=0, le=1)
    parcel_demand_index: float = Field(..., ge=0, le=1)
    historical_income_variance: float = Field(..., ge=0, le=1)
    active_hours_ratio: float = Field(..., ge=0, le=1)
    gps_jump_distance: float = Field(..., ge=0)
    claim_frequency_7day: float = Field(..., ge=0)
    nearby_claim_cluster_score: float = Field(..., ge=0, le=1)


class IncomeLossResponse(BaseModel):
    expected_income_loss_hours: float
    severity_level: str
    model_version: str = "xgb_reg_v1"


class FraudDetectionRequest(BaseModel):
    """Input features for fraud detection."""
    gps_jump_distance: float = Field(..., ge=0, description="GPS jump distance in km")
    claim_frequency_7day: float = Field(..., ge=0, description="Claims in last 7 days")
    active_hours_ratio: float = Field(..., ge=0, le=1, description="Active hours 0-1")
    nearby_claim_cluster_score: float = Field(..., ge=0, le=1, description="Cluster score 0-1")


class FraudDetectionResponse(BaseModel):
    fraud_anomaly_score: float
    is_suspicious: bool
    risk_level: str
    threshold_used: float
    model_version: str = "iforest_v1"


class TrustScoreRequest(BaseModel):
    """Input for trust score computation."""
    mobility_stability_index: float = Field(..., ge=0, le=1)
    behavioral_trust_index: float = Field(..., ge=0, le=1)
    fraud_anomaly_score: float = Field(..., ge=0, le=1)
    disruption_risk_score: float = Field(..., ge=0, le=1)


class TrustScoreResponse(BaseModel):
    trust_score: float
    genuine_disruption_probability: float
    recommendation: str
    explanation: str
    component_scores: dict


# ─── Feature Engineering Helpers ────────────────────────────

def _engineer_features(data: dict) -> np.ndarray:
    """Compute derived features from raw input and return full feature vector."""
    rain_norm = data["rainfall_last_3day_avg"] / 350.0
    
    # disruption_risk_score_feature
    disruption_risk = min(1.0,
        rain_norm * 0.35 +
        data["flood_zone_flag"] * 0.25 +
        data["traffic_peak_index"] * 0.25 +
        data["pollution_spike_flag"] * 0.15
    )
    
    # mobility_stability_index
    gps_stability = max(0, 1.0 - data["gps_jump_distance"] / 80.0)
    mobility_stability = min(1.0, gps_stability * 0.6 + data["active_hours_ratio"] * 0.4)
    
    # logistics_volatility_feature
    demand_dev = abs(data["parcel_demand_index"] - 0.65)
    logistics_vol = min(1.0, demand_dev * 1.2 + data["historical_income_variance"] * 0.5)
    
    # behavioral_trust_index
    claim_norm = min(1.0, data["claim_frequency_7day"] / 10.0)
    behavioral_trust = min(1.0,
        data["active_hours_ratio"] * 0.35 +
        (1.0 - claim_norm) * 0.35 +
        (1.0 - data["nearby_claim_cluster_score"]) * 0.30
    )
    
    # Interaction features
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
    
    return np.array(feature_vector).reshape(1, -1)


# ─── Endpoints ──────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "ShieldPay AI — ML Intelligence API",
        "version": "1.0.0",
        "models_loaded": list(models.keys()),
        "status": "operational",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "models": len(models)}


@app.post("/predict-risk", response_model=RiskPredictionResponse, tags=["Risk Prediction"])
async def predict_risk(request: RiskPredictionRequest):
    """
    Predict income loss risk for a delivery worker.
    Uses trained XGBoost classifier on environmental + behavioral features.
    """
    if "risk_model" not in models:
        raise HTTPException(status_code=503, detail="Risk model not loaded. Run training pipeline first.")
    
    model = models["risk_model"]
    features = _engineer_features(request.model_dump())
    
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
    
    return RiskPredictionResponse(
        high_risk=bool(prediction),
        risk_probability=round(probability, 4),
        risk_level=risk_level,
    )


@app.post("/predict-income-loss", response_model=IncomeLossResponse, tags=["Income Loss"])
async def predict_income_loss(request: IncomeLossRequest):
    """
    Predict expected income loss hours for next week.
    Uses trained XGBoost regressor on delivery disruption features.
    """
    if "income_loss_model" not in models:
        raise HTTPException(status_code=503, detail="Income loss model not loaded.")
    
    model = models["income_loss_model"]
    features = _engineer_features(request.model_dump())
    
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
    
    return IncomeLossResponse(
        expected_income_loss_hours=predicted_hours,
        severity_level=severity,
    )


@app.post("/detect-fraud", response_model=FraudDetectionResponse, tags=["Fraud Detection"])
async def detect_fraud(request: FraudDetectionRequest):
    """
    Detect fraudulent claim patterns using IsolationForest anomaly detection.
    Analyzes GPS behavior, claim patterns, activity levels, and clustering.
    """
    if "fraud_model" not in models:
        raise HTTPException(status_code=503, detail="Fraud model not loaded.")
    if "fraud_scaler" not in models:
        raise HTTPException(status_code=503, detail="Fraud scaler not loaded.")
    
    model = models["fraud_model"]
    scaler = models["fraud_scaler"]
    
    features = np.array([[
        request.gps_jump_distance,
        request.claim_frequency_7day,
        request.active_hours_ratio,
        request.nearby_claim_cluster_score,
    ]])
    
    features_scaled = scaler.transform(features)
    
    # Decision function: lower = more anomalous
    raw_score = model.decision_function(features_scaled)[0]
    prediction = model.predict(features_scaled)[0]
    
    # Load threshold from metrics
    fraud_metrics = models.get("fraud_model_metrics", {})
    threshold = fraud_metrics.get("optimal_threshold", 0.92)
    
    # Normalize to 0-1 anomaly score (approximate using training distribution)
    # In production, you'd use the exact training distribution bounds
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
    
    return FraudDetectionResponse(
        fraud_anomaly_score=round(anomaly_score, 4),
        is_suspicious=bool(is_suspicious),
        risk_level=risk_level,
        threshold_used=threshold,
    )


@app.post("/calculate-trust-score", response_model=TrustScoreResponse, tags=["Trust Score"])
async def calculate_trust_score(request: TrustScoreRequest):
    """
    Calculate composite trust score for claim verification.
    Combines mobility, behavioral, fraud, and disruption signals.
    """
    from ai_pipeline.trust_engine import compute_trust_score
    
    result = compute_trust_score(
        mobility_stability_index=request.mobility_stability_index,
        behavioral_trust_index=request.behavioral_trust_index,
        fraud_anomaly_score=request.fraud_anomaly_score,
        disruption_risk_score=request.disruption_risk_score,
    )
    
    return TrustScoreResponse(**result)


# ─── Run server ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting ShieldPay AI ML Inference Server...")
    uvicorn.run(
        "ai_pipeline.api_server:app",
        host="0.0.0.0",
        port=8100,
        reload=True,
    )
