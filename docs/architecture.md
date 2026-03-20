# ShieldPay AI — System Architecture

## Overview

ShieldPay AI is a **parametric micro-insurance platform** that protects e-commerce delivery workers (Amazon/Flipkart last-mile partners) in India from **income loss caused by external operational disruptions**. The system uses AI-driven risk intelligence, automated parametric triggers, and multi-layer fraud detection to deliver instant, fair payouts.

## System Design Diagram

```mermaid
graph TB
    subgraph "Frontend Layer"
        WD["Worker Dashboard<br/>Coverage • Claims • Risk Meter"]
        AD["Admin Panel<br/>Fraud Heatmap • Analytics • Alerts"]
    end

    subgraph "API Gateway"
        FW["FastAPI Gateway<br/>JWT Auth • RBAC • Rate Limiting"]
    end

    subgraph "Core Microservices"
        AUTH["Auth Service<br/>JWT • Roles"]
        WRK["Worker Service<br/>Registration • Profiles"]
        POL["Policy Service<br/>Purchase • Renewal"]
        CLM["Claims Service<br/>Submit • Track • Payout"]
        PAY["Payment Simulation<br/>Premium • Payout"]
    end

    subgraph "AI Services"
        RISK["Risk Intelligence Engine<br/>Disruption Prediction"]
        INC["Income Forecast Model<br/>7-Day Parcel Prediction"]
        PREM["Premium Optimizer<br/>Dynamic Weekly Pricing"]
        FRAUD["Fraud Detection Pipeline<br/>Graph ML • Anomaly Scoring"]
        TRUST["Trust Score Engine<br/>Multi-Signal Verification"]
    end

    subgraph "Automation Layer"
        SCHED["Trigger Scheduler<br/>20-Min Interval Scan"]
        AUTO["Claim Automation<br/>Parametric Flow"]
        THROT["Payout Throttle<br/>Liquidity Protection"]
    end

    subgraph "External APIs"
        WAPI["Weather API<br/>OpenWeatherMap"]
        TAPI["Traffic API<br/>TomTom / Google"]
        LAPI["Logistics Mock API<br/>Warehouse Disruptions"]
    end

    subgraph "Data Layer"
        MONGO["MongoDB Atlas<br/>Workers • Policies • Claims"]
        REDIS["Redis Cache<br/>Trigger State • Sessions"]
        LOGS["Event Logs<br/>Audit Trail"]
    end

    WD & AD --> FW
    FW --> AUTH & WRK & POL & CLM & PAY
    CLM --> TRUST --> FRAUD
    POL --> PREM --> RISK
    RISK --> INC
    SCHED --> AUTO --> CLM
    AUTO --> THROT
    RISK --> WAPI & TAPI & LAPI
    AUTH & WRK & POL & CLM --> MONGO
    SCHED --> REDIS
    CLM & FRAUD --> LOGS
```

## Data Flow: Parametric Claim Lifecycle

```mermaid
sequenceDiagram
    participant S as Scheduler (20min)
    participant E as External APIs
    participant R as Risk Engine
    participant T as Trust Scorer
    participant F as Fraud Detector
    participant C as Claims Service
    participant P as Payout

    S->>E: Fetch weather, traffic, logistics data
    E-->>S: Environmental signals
    S->>R: Evaluate disruption triggers
    R-->>S: Disruption detected (warehouse X flooded)
    S->>C: Create parametric claim for affected workers
    C->>T: Evaluate worker trust score
    T->>F: Run fraud detection layers
    F-->>T: Fraud anomaly score
    T-->>C: claim_approval_probability
    alt Trust > 0.85
        C->>P: INSTANT PAYOUT
    else Trust 0.5-0.85
        C->>C: SOFT VERIFICATION (in-app confirm)
    else Trust < 0.5
        C->>C: DELAYED REVIEW (manual check)
    end
```

## Trust Score Model

```
claim_approval_probability = weighted(
    real_movement_score      × 0.25,
    delivery_activity_score  × 0.25,
    environmental_match_score × 0.20,
    historical_trust_index   × 0.15,
    fraud_anomaly_score      × 0.15
)
```

### Multi-Layer Fraud Defense

| Layer | Signals | Detection Method |
|-------|---------|-----------------|
| **Behavioral Movement** | Accelerometer, route continuity, teleport detection | Time-series anomaly detection |
| **Delivery Correlation** | Parcels assigned vs delivered, warehouse dependency | Statistical deviation analysis |
| **Environmental Consensus** | Disruption clustering, telecom degradation, traffic | Cross-worker correlation |
| **Device Authenticity** | Emulator/root flags, background streaming, app fingerprint | Device integrity scoring |
| **Graph Fraud Rings** | Temporal claim spikes, network connections | Graph ML community detection |

## Premium Pricing Formula

```
premium = base_price + (predicted_income_volatility × risk_multiplier)

Where:
  base_price = ₹15-50/week based on coverage tier
  predicted_income_volatility = AI-forecast of parcel volume variance
  risk_multiplier = composite risk score (weather + traffic + warehouse + seasonal)
```

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Frontend | React 18 + Vite, Recharts, CSS3 |
| Backend | FastAPI, Python 3.11+ |
| Auth | JWT + bcrypt, RBAC |
| Database | MongoDB (motor async driver) |
| Cache | Redis |
| AI/ML | scikit-learn, NetworkX |
| Scheduler | APScheduler |
| External | OpenWeatherMap, TomTom, Mock APIs |
