"""
ShieldPay AI — Scenario-Driven Synthetic Dataset Generator
===========================================================
Produces 8000+ rows of CORRELATED synthetic data modeling realistic
causal relationships in delivery logistics risk:

Causal graph:
  • higher rainfall → higher traffic congestion
  • flood zone → higher claim probability
  • high parcel demand volatility → income instability  
  • fraud clusters → sudden GPS jump variance
  • low activity + high claim frequency → anomaly pattern
  • city risk drives environmental baseline
  • pollution spikes correlate with traffic/weather

Output: data/synthetic_delivery_risk.csv
"""

import numpy as np
import pandas as pd
import os
from pathlib import Path


# ─── Configuration ─────────────────────────────────────────
NUM_ROWS = 8500
SEED = 42
OUTPUT_DIR = Path(__file__).parent / "data"

# City profiles: (name, base_risk, flood_prob, avg_rainfall, traffic_base)
CITY_PROFILES = [
    ("Mumbai",    0.72, 0.40, 85,  0.80),
    ("Delhi",     0.55, 0.10, 25,  0.75),
    ("Bangalore", 0.48, 0.15, 55,  0.85),
    ("Chennai",   0.68, 0.35, 70,  0.65),
    ("Kolkata",   0.65, 0.30, 75,  0.70),
    ("Pune",      0.40, 0.12, 40,  0.55),
    ("Hyderabad", 0.45, 0.18, 45,  0.60),
    ("Ahmedabad", 0.38, 0.08, 15,  0.50),
]


def generate_dataset(n_rows: int = NUM_ROWS, seed: int = SEED) -> pd.DataFrame:
    """
    Generate correlated synthetic delivery risk data.
    
    The data is NOT random noise — each column is derived from
    an underlying causal structure that mirrors real-world logistics.
    """
    rng = np.random.default_rng(seed)
    
    # ── 1. Assign workers to cities with risk profiles ──────
    city_indices = rng.integers(0, len(CITY_PROFILES), size=n_rows)
    city_names   = [CITY_PROFILES[i][0] for i in city_indices]
    base_risk    = np.array([CITY_PROFILES[i][1] for i in city_indices])
    flood_prob   = np.array([CITY_PROFILES[i][2] for i in city_indices])
    avg_rainfall = np.array([CITY_PROFILES[i][3] for i in city_indices])
    traffic_base = np.array([CITY_PROFILES[i][4] for i in city_indices])
    
    # Worker IDs
    worker_ids = [f"WRK-{i+1:05d}" for i in range(n_rows)]
    
    # ── 2. city_risk_index ──────────────────────────────────
    # Base risk + seasonal noise
    city_risk_index = np.clip(
        base_risk + rng.normal(0, 0.08, n_rows),
        0.05, 0.99
    )
    
    # ── 3. rainfall_last_3day_avg (mm) ──────────────────────
    # Driven by city profile + seasonal noise + extreme events
    rainfall_last_3day_avg = np.clip(
        avg_rainfall + rng.exponential(scale=avg_rainfall * 0.3, size=n_rows)
        + rng.normal(0, 10, n_rows),
        0, 350
    )
    
    # ── 4. flood_zone_flag ──────────────────────────────────
    # Probability driven by city + boosted when rainfall is extreme
    rainfall_boost = np.where(rainfall_last_3day_avg > 100, 0.25, 0.0)
    flood_zone_flag = (rng.random(n_rows) < (flood_prob + rainfall_boost)).astype(int)
    
    # ── 5. traffic_peak_index ───────────────────────────────
    # CAUSAL: higher rainfall → higher traffic congestion
    rainfall_effect = 0.003 * rainfall_last_3day_avg  # rainfall drives congestion
    traffic_peak_index = np.clip(
        traffic_base + rainfall_effect + rng.normal(0, 0.08, n_rows),
        0.1, 1.0
    )
    
    # ── 6. pollution_spike_flag ─────────────────────────────
    # Correlates with traffic and low rainfall (rain cleans air)
    pollution_prob = np.where(
        (traffic_peak_index > 0.7) & (rainfall_last_3day_avg < 30),
        0.55,
        0.15
    )
    pollution_spike_flag = (rng.random(n_rows) < pollution_prob).astype(int)
    
    # ── 7. parcel_demand_index ──────────────────────────────
    # City-dependent + disruption suppression
    parcel_demand_base = rng.uniform(0.3, 1.0, n_rows)
    disruption_suppress = np.where(flood_zone_flag == 1, -0.2, 0.0) + \
                          np.where(traffic_peak_index > 0.85, -0.15, 0.0)
    parcel_demand_index = np.clip(
        parcel_demand_base + disruption_suppress + rng.normal(0, 0.05, n_rows),
        0.05, 1.0
    )
    
    # ── 8. historical_income_variance ───────────────────────
    # CAUSAL: high parcel demand volatility → income instability
    demand_volatility = np.abs(parcel_demand_index - 0.65)  # deviation from median
    historical_income_variance = np.clip(
        demand_volatility * 2.5 + rng.exponential(0.15, n_rows),
        0.01, 1.0
    )
    
    # ── 9. active_hours_ratio (0-1) ─────────────────────────
    # Normal workers: 0.5-0.95, fraud pattern: some have very low activity
    active_hours_ratio = np.clip(
        rng.beta(5, 2, n_rows) * 0.8 + 0.15,
        0.05, 0.99
    )
    
    # ── 10. Fraud cluster injection (~8% of workers) ────────
    n_fraud = int(n_rows * 0.08)
    fraud_mask = np.zeros(n_rows, dtype=bool)
    fraud_indices = rng.choice(n_rows, size=n_fraud, replace=False)
    fraud_mask[fraud_indices] = True
    
    # ── 11. gps_jump_distance (km) ──────────────────────────
    # CAUSAL: fraud clusters → sudden GPS jump variance
    gps_jump_normal = rng.exponential(scale=2.0, size=n_rows)
    gps_jump_fraud  = rng.exponential(scale=25.0, size=n_rows) + rng.uniform(10, 60, n_rows)
    gps_jump_distance = np.where(fraud_mask, gps_jump_fraud, gps_jump_normal)
    gps_jump_distance = np.clip(gps_jump_distance, 0.0, 150.0)
    
    # ── 12. claim_frequency_7day ────────────────────────────
    # CAUSAL: flood zone → higher claim probability
    #         fraud actors → inflated claim rates
    base_claim_rate = np.where(flood_zone_flag == 1, 2.5, 0.8)
    env_boost = np.where(rainfall_last_3day_avg > 80, 1.2, 0.0)
    fraud_boost = np.where(fraud_mask, rng.uniform(3, 8, n_rows), 0.0)
    claim_frequency_7day = np.clip(
        rng.poisson(base_claim_rate + env_boost, n_rows) + fraud_boost,
        0, 15
    ).astype(float)
    
    # Fraud pattern: low activity + high claims = anomaly
    active_hours_ratio[fraud_mask] = np.clip(
        rng.uniform(0.05, 0.35, n_fraud),
        0.05, 0.40
    )
    
    # ── 13. nearby_claim_cluster_score ──────────────────────
    # Fraud clusters have correlated high scores
    nearby_base = rng.uniform(0.0, 0.4, n_rows)
    nearby_fraud = rng.uniform(0.6, 1.0, n_rows)  
    nearby_claim_cluster_score = np.where(fraud_mask, nearby_fraud, nearby_base)
    # Also boost for genuine high-disruption areas
    genuine_boost = np.where(
        (flood_zone_flag == 1) & (rainfall_last_3day_avg > 100),
        rng.uniform(0.1, 0.3, n_rows),
        0.0
    )
    nearby_claim_cluster_score = np.clip(
        nearby_claim_cluster_score + genuine_boost,
        0.0, 1.0
    )
    
    # ── 14. income_loss_hours (TARGET) ──────────────────────
    # Driven by: environmental disruption + fraud inflation
    environmental_loss = (
        city_risk_index * 3.0 +
        np.where(flood_zone_flag == 1, rng.uniform(4, 12, n_rows), 0.0) +
        np.where(rainfall_last_3day_avg > 80, rainfall_last_3day_avg * 0.04, 0.0) +
        np.where(traffic_peak_index > 0.8, rng.uniform(1, 5, n_rows), 0.0) +
        historical_income_variance * 2.0
    )
    # Fraud actors inflate losses
    fraud_inflation = np.where(fraud_mask, rng.uniform(8, 25, n_rows), 0.0)
    
    income_loss_hours = np.clip(
        environmental_loss + fraud_inflation + rng.normal(0, 1.5, n_rows),
        0.0, 50.0
    )
    
    # ── Build DataFrame ─────────────────────────────────────
    df = pd.DataFrame({
        "worker_id":                  worker_ids,
        "city_risk_index":            np.round(city_risk_index, 4),
        "rainfall_last_3day_avg":     np.round(rainfall_last_3day_avg, 2),
        "flood_zone_flag":            flood_zone_flag,
        "traffic_peak_index":         np.round(traffic_peak_index, 4),
        "pollution_spike_flag":       pollution_spike_flag,
        "parcel_demand_index":        np.round(parcel_demand_index, 4),
        "historical_income_variance": np.round(historical_income_variance, 4),
        "active_hours_ratio":         np.round(active_hours_ratio, 4),
        "gps_jump_distance":          np.round(gps_jump_distance, 2),
        "claim_frequency_7day":       np.round(claim_frequency_7day, 1),
        "nearby_claim_cluster_score": np.round(nearby_claim_cluster_score, 4),
        "income_loss_hours":          np.round(income_loss_hours, 2),
    })
    
    return df


def save_dataset(df: pd.DataFrame, output_dir: Path = OUTPUT_DIR) -> str:
    """Save dataset to CSV."""
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / "synthetic_delivery_risk.csv"
    df.to_csv(filepath, index=False)
    return str(filepath)


def print_summary(df: pd.DataFrame):
    """Print dataset quality summary."""
    print("=" * 60)
    print("  ShieldPay AI — Synthetic Delivery Risk Dataset")
    print("=" * 60)
    print(f"\n📊 Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"\n📋 Columns:\n  {', '.join(df.columns)}")
    
    print(f"\n🔗 Correlation Checks (causal relationships):")
    r_rain_traffic = df["rainfall_last_3day_avg"].corr(df["traffic_peak_index"])
    r_flood_claims = df["flood_zone_flag"].corr(df["claim_frequency_7day"])
    r_demand_income = df["parcel_demand_index"].corr(df["historical_income_variance"])
    r_gps_cluster = df["gps_jump_distance"].corr(df["nearby_claim_cluster_score"])
    r_activity_claims = df["active_hours_ratio"].corr(df["claim_frequency_7day"])
    
    print(f"  rainfall → traffic:     r = {r_rain_traffic:+.3f}  (expect positive)")
    print(f"  flood → claims:         r = {r_flood_claims:+.3f}  (expect positive)")
    print(f"  demand → income_var:    r = {r_demand_income:+.3f}  (expect correlation)")
    print(f"  gps_jump → cluster:     r = {r_gps_cluster:+.3f}  (expect positive)")
    print(f"  activity → claims:      r = {r_activity_claims:+.3f}  (expect negative)")
    
    print(f"\n📈 Target Distribution (income_loss_hours):")
    print(f"  Mean:   {df['income_loss_hours'].mean():.2f}")
    print(f"  Median: {df['income_loss_hours'].median():.2f}")
    print(f"  Std:    {df['income_loss_hours'].std():.2f}")
    print(f"  Min:    {df['income_loss_hours'].min():.2f}")
    print(f"  Max:    {df['income_loss_hours'].max():.2f}")
    
    print(f"\n🎭 Fraud Pattern Check:")
    high_gps = (df["gps_jump_distance"] > 15).sum()
    low_activity_high_claims = (
        (df["active_hours_ratio"] < 0.35) & (df["claim_frequency_7day"] > 3)
    ).sum()
    print(f"  High GPS jumps (>15km): {high_gps} ({100*high_gps/len(df):.1f}%)")
    print(f"  Low activity + high claims: {low_activity_high_claims} ({100*low_activity_high_claims/len(df):.1f}%)")
    
    print(f"\n✅ Dataset generation complete!")


if __name__ == "__main__":
    df = generate_dataset()
    filepath = save_dataset(df)
    print_summary(df)
    print(f"\n💾 Saved to: {filepath}")
