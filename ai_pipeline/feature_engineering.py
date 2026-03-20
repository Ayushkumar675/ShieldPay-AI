"""
ShieldPay AI — Feature Engineering Pipeline
=============================================
Transforms raw synthetic data into ML-ready features with domain-driven
derived columns and proper scaling.

Derived Features:
  • disruption_risk_score_feature — composite environmental disruption signal
  • mobility_stability_index — GPS stability × active hours consistency  
  • logistics_volatility_feature — demand variance × income variance
  • behavioral_trust_index — low claims × high activity × low clustering
"""

import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.preprocessing import StandardScaler, MinMaxScaler


DATA_DIR = Path(__file__).parent / "data"
MODELS_DIR = Path(__file__).parent / "models" / "saved"


def load_raw_data(filepath: str = None) -> pd.DataFrame:
    """Load the raw synthetic dataset."""
    if filepath is None:
        filepath = DATA_DIR / "synthetic_delivery_risk.csv"
    df = pd.read_csv(filepath)
    print(f"✅ Loaded {len(df)} rows from {filepath}")
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate all derived features from raw columns.
    Each feature has clear domain semantics.
    """
    df = df.copy()
    
    # ── 1. disruption_risk_score_feature ────────────────────
    # Composite of environmental disruption signals
    # Captures: rainfall severity + flood exposure + traffic severity + pollution
    df["disruption_risk_score_feature"] = np.clip(
        (
            df["rainfall_last_3day_avg"] / 350.0 * 0.35 +       # Normalized rainfall contribution
            df["flood_zone_flag"] * 0.25 +                       # Binary flood zone boost
            df["traffic_peak_index"] * 0.25 +                     # Traffic congestion contribution
            df["pollution_spike_flag"] * 0.15                     # Pollution event contribution
        ),
        0.0, 1.0
    )
    
    # ── 2. mobility_stability_index ─────────────────────────
    # Low GPS variance + consistent active hours = stable mobility
    # Inverted GPS jump: lower jump = higher stability
    max_gps = df["gps_jump_distance"].quantile(0.99)  # Robust normalization
    gps_stability = 1.0 - np.clip(df["gps_jump_distance"] / max_gps, 0, 1)
    
    df["mobility_stability_index"] = np.clip(
        gps_stability * 0.6 + df["active_hours_ratio"] * 0.4,
        0.0, 1.0
    )
    
    # ── 3. logistics_volatility_feature ─────────────────────
    # High parcel demand deviation + high income variance = volatile logistics
    demand_deviation = np.abs(df["parcel_demand_index"] - df["parcel_demand_index"].median())
    demand_deviation_norm = demand_deviation / demand_deviation.max()
    
    df["logistics_volatility_feature"] = np.clip(
        demand_deviation_norm * 0.5 + df["historical_income_variance"] * 0.5,
        0.0, 1.0
    )
    
    # ── 4. behavioral_trust_index ───────────────────────────
    # Genuine workers: high activity, low claim frequency, low cluster score
    # Fraudulent workers: low activity, high claims, high cluster score
    claim_max = df["claim_frequency_7day"].quantile(0.99)
    claim_norm = np.clip(df["claim_frequency_7day"] / max(claim_max, 1), 0, 1)
    
    df["behavioral_trust_index"] = np.clip(
        df["active_hours_ratio"] * 0.35 +
        (1.0 - claim_norm) * 0.35 +
        (1.0 - df["nearby_claim_cluster_score"]) * 0.30,
        0.0, 1.0
    )
    
    # ── 5. Interaction features ─────────────────────────────
    # rainfall × traffic interaction (compounding disruption)
    df["rain_traffic_interaction"] = (
        df["rainfall_last_3day_avg"] / 350.0 * df["traffic_peak_index"]
    )
    
    # flood × claim interaction (genuine disruption claims)
    df["flood_claim_interaction"] = (
        df["flood_zone_flag"] * df["claim_frequency_7day"] / max(claim_max, 1)
    )
    
    # GPS anomaly × claim ratio (fraud signal)
    df["gps_claim_anomaly"] = (
        np.clip(df["gps_jump_distance"] / max_gps, 0, 1) *
        claim_norm
    )
    
    print(f"✅ Engineered {4 + 3} derived features")
    return df


def create_target_variables(df: pd.DataFrame, loss_threshold: float = 8.0) -> pd.DataFrame:
    """
    Create target variables for classification and regression.
    
    Args:
        loss_threshold: hours above which we flag as high-risk (tuned for ~30% positive rate)
    """
    df = df.copy()
    
    # Binary classification target
    df["high_income_loss_risk_flag"] = (df["income_loss_hours"] > loss_threshold).astype(int)
    
    # Regression target (simulated next-week projection)
    # Apply small noise to simulate temporal projection
    rng = np.random.default_rng(42)
    weekly_factor = rng.uniform(0.8, 1.4, len(df))  # Weekly variation 
    df["expected_income_loss_hours_next_week"] = np.clip(
        df["income_loss_hours"] * weekly_factor + rng.normal(0, 1.0, len(df)),
        0.0, 60.0
    )
    
    pos_rate = df["high_income_loss_risk_flag"].mean()
    print(f"✅ Classification target: {pos_rate:.1%} positive rate (threshold={loss_threshold}h)")
    print(f"✅ Regression target: mean={df['expected_income_loss_hours_next_week'].mean():.2f}h")
    
    return df


def scale_features(df: pd.DataFrame, fit: bool = True) -> tuple:
    """
    Apply StandardScaler to numeric features.
    Returns (scaled_df, scaler).
    """
    # Feature columns for scaling (exclude IDs, targets, and binary flags)
    scale_cols = [
        "city_risk_index", "rainfall_last_3day_avg", "traffic_peak_index",
        "parcel_demand_index", "historical_income_variance", "active_hours_ratio",
        "gps_jump_distance", "claim_frequency_7day", "nearby_claim_cluster_score",
        "disruption_risk_score_feature", "mobility_stability_index",
        "logistics_volatility_feature", "behavioral_trust_index",
        "rain_traffic_interaction", "flood_claim_interaction", "gps_claim_anomaly",
    ]
    
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    if fit:
        scaler = StandardScaler()
        df[scale_cols] = scaler.fit_transform(df[scale_cols])
        scaler_path = MODELS_DIR / "feature_scaler.pkl"
        joblib.dump(scaler, scaler_path)
        print(f"✅ Scaler fitted and saved to {scaler_path}")
    else:
        scaler_path = MODELS_DIR / "feature_scaler.pkl"
        scaler = joblib.load(scaler_path)
        df[scale_cols] = scaler.transform(df[scale_cols])
        print(f"✅ Scaler loaded from {scaler_path}")
    
    return df, scaler


def get_feature_columns() -> list:
    """Return the list of feature columns used for modeling."""
    return [
        "city_risk_index", "rainfall_last_3day_avg", "flood_zone_flag",
        "traffic_peak_index", "pollution_spike_flag", "parcel_demand_index",
        "historical_income_variance", "active_hours_ratio", "gps_jump_distance",
        "claim_frequency_7day", "nearby_claim_cluster_score",
        "disruption_risk_score_feature", "mobility_stability_index",
        "logistics_volatility_feature", "behavioral_trust_index",
        "rain_traffic_interaction", "flood_claim_interaction", "gps_claim_anomaly",
    ]


def get_fraud_feature_columns() -> list:
    """Return feature columns for fraud detection model."""
    return [
        "gps_jump_distance", "claim_frequency_7day",
        "active_hours_ratio", "nearby_claim_cluster_score",
    ]


def run_pipeline(input_path: str = None) -> pd.DataFrame:
    """Full feature engineering pipeline."""
    print("=" * 60)
    print("  ShieldPay AI — Feature Engineering Pipeline")
    print("=" * 60)
    
    df = load_raw_data(input_path)
    df = engineer_features(df)
    df = create_target_variables(df)
    
    # Save engineered (unscaled) dataset for transparency
    engineered_path = DATA_DIR / "engineered_features.csv"
    df.to_csv(engineered_path, index=False)
    print(f"💾 Saved engineered features to {engineered_path}")
    
    # Save scaled version
    df_scaled, scaler = scale_features(df.copy(), fit=True)
    scaled_path = DATA_DIR / "scaled_features.csv"
    df_scaled.to_csv(scaled_path, index=False)
    print(f"💾 Saved scaled features to {scaled_path}")
    
    print(f"\n✅ Feature engineering complete!")
    print(f"   Raw features: 13 → Engineered: {len(get_feature_columns())} columns")
    
    return df


if __name__ == "__main__":
    run_pipeline()
