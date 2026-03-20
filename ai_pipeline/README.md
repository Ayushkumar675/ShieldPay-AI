# ShieldPay AI — ML Intelligence Pipeline

Production-grade ML pipeline for parametric insurance: risk prediction, income loss estimation, fraud detection, and trust scoring for delivery workers.

## Architecture

```
ai_pipeline/
├── data_generator.py          # Step 1: Correlated synthetic data (8500 rows)
├── feature_engineering.py     # Step 2: 18 derived features + scaling
├── models/
│   ├── risk_model.py          # Step 3: XGBoost classifier (risk prediction)
│   ├── income_loss_model.py   # Step 4: XGBoost regressor (income loss)
│   ├── fraud_model.py         # Step 5: IsolationForest (fraud detection)
│   └── saved/                 # Trained .pkl model files
├── trust_engine.py            # Step 6: Trust score fusion engine
├── api_server.py              # Step 7: FastAPI inference server (port 8100)
├── scheduler.py               # Step 8: Parametric automation scheduler
├── evaluation_report.py       # Step 9: Auto-generated evaluation report
├── run_pipeline.py            # Master pipeline runner (Steps 1-6)
├── data/                      # Generated CSV datasets
├── reports/                   # Plots, metrics JSON, evaluation report
├── logs/                      # Scheduler decision logs
└── requirements.txt           # Python dependencies
```

## Quick Start

```bash
# 1. Install dependencies
cd "ShieldPay AI"
pip install -r ai_pipeline/requirements.txt

# 2. Run full training pipeline (data → features → train → report)
python -m ai_pipeline.run_pipeline

# 3. Start API server
python -m ai_pipeline.api_server

# 4. Run parametric scheduler (3 cycles)
python -m ai_pipeline.scheduler
```

## API Endpoints (port 8100)

### POST /predict-risk
```json
{
  "city_risk_index": 0.72,
  "rainfall_last_3day_avg": 120.5,
  "flood_zone_flag": 1,
  "traffic_peak_index": 0.85,
  "pollution_spike_flag": 0,
  "parcel_demand_index": 0.45,
  "historical_income_variance": 0.35,
  "active_hours_ratio": 0.75,
  "gps_jump_distance": 3.2,
  "claim_frequency_7day": 2.0,
  "nearby_claim_cluster_score": 0.15
}
```
**Response:**
```json
{
  "high_risk": true,
  "risk_probability": 0.8234,
  "risk_level": "critical",
  "model_version": "xgb_v1"
}
```

### POST /predict-income-loss
Same input schema → returns `expected_income_loss_hours` + `severity_level`

### POST /detect-fraud
```json
{
  "gps_jump_distance": 45.0,
  "claim_frequency_7day": 7.0,
  "active_hours_ratio": 0.15,
  "nearby_claim_cluster_score": 0.85
}
```
**Response:**
```json
{
  "fraud_anomaly_score": 0.87,
  "is_suspicious": true,
  "risk_level": "critical",
  "threshold_used": 0.92,
  "model_version": "iforest_v1"
}
```

### POST /calculate-trust-score
```json
{
  "mobility_stability_index": 0.85,
  "behavioral_trust_index": 0.90,
  "fraud_anomaly_score": 0.10,
  "disruption_risk_score": 0.80
}
```
**Response:**
```json
{
  "trust_score": 0.8325,
  "genuine_disruption_probability": 0.8325,
  "recommendation": "AUTO_APPROVE",
  "explanation": "High trust — genuine disruption pattern detected.",
  "component_scores": { ... }
}
```

## Models

| Model | Type | Target | Algorithm |
|-------|------|--------|-----------|
| Risk | Classification | `high_income_loss_risk_flag` | XGBoost |
| Income Loss | Regression | `expected_income_loss_hours_next_week` | XGBoost |
| Fraud | Anomaly Detection | `fraud_anomaly_score` | IsolationForest |
| Trust | Fusion | `trust_score` | Weighted Composite |
