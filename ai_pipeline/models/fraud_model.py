"""
ShieldPay AI — Fraud Detection Model (IsolationForest)
=======================================================
Anomaly detection for identifying fraudulent claim patterns.

Features used:
  • gps_jump_distance — GPS teleportation detection
  • claim_frequency_7day — claim volume anomaly
  • active_hours_ratio — activity level (low = suspicious)
  • nearby_claim_cluster_score — coordinated fraud signal

Output: fraud_anomaly_score per worker
Threshold: percentile-based classification of suspicious claims

Saved: models/saved/fraud_iforest.pkl
"""

import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import json
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score

MODELS_DIR = Path(__file__).parent / "saved"
REPORTS_DIR = Path(__file__).parent.parent / "reports"
DATA_DIR = Path(__file__).parent.parent / "data"


FRAUD_FEATURES = [
    "gps_jump_distance",
    "claim_frequency_7day",
    "active_hours_ratio",
    "nearby_claim_cluster_score",
]


def train_fraud_model():
    """Full training pipeline for fraud anomaly detection."""
    print("=" * 60)
    print("  ShieldPay AI — Fraud Detection Model Training")
    print("=" * 60)
    
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load data
    df = pd.read_csv(DATA_DIR / "engineered_features.csv")
    
    X = df[FRAUD_FEATURES].copy()
    
    # ── 1. Scale features for IsolationForest ───────────────
    print("\n🔧 Step 1: Feature Scaling")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Save fraud-specific scaler
    scaler_path = MODELS_DIR / "fraud_scaler.pkl"
    joblib.dump(scaler, scaler_path)
    print(f"  💾 Scaler saved to {scaler_path}")
    
    # ── 2. Train IsolationForest ────────────────────────────
    print("\n🌲 Step 2: IsolationForest Training")
    # contamination roughly matches our ~8% fraud rate
    model = IsolationForest(
        n_estimators=200,
        max_samples="auto",
        contamination=0.08,
        max_features=1.0,
        bootstrap=False,
        random_state=42,
        n_jobs=-1,
    )
    
    model.fit(X_scaled)
    print(f"  ✅ Model trained on {len(X_scaled)} samples")
    
    # ── 3. Generate anomaly scores ──────────────────────────
    print("\n📈 Step 3: Anomaly Score Generation")
    # decision_function: lower = more anomalous
    raw_scores = model.decision_function(X_scaled)
    
    # Convert to 0-1 anomaly score (higher = more suspicious)
    # IsolationForest: negative scores = anomalous
    fraud_anomaly_score = 1.0 - (raw_scores - raw_scores.min()) / (raw_scores.max() - raw_scores.min())
    
    df["fraud_anomaly_score"] = np.round(fraud_anomaly_score, 4)
    
    # Predictions: -1 = anomaly, 1 = normal
    predictions = model.predict(X_scaled)
    df["fraud_predicted"] = (predictions == -1).astype(int)
    
    # ── 4. Threshold analysis ───────────────────────────────
    print("\n🎯 Step 4: Threshold Analysis")
    
    # Determine optimal threshold using percentile
    percentiles = [85, 90, 92, 95, 97]
    threshold_analysis = []
    
    for pct in percentiles:
        threshold = np.percentile(fraud_anomaly_score, pct)
        flagged = (fraud_anomaly_score >= threshold).sum()
        pct_flagged = flagged / len(fraud_anomaly_score) * 100
        
        threshold_analysis.append({
            "percentile": pct,
            "threshold": round(float(threshold), 4),
            "flagged_count": int(flagged),
            "flagged_pct": round(pct_flagged, 2),
        })
        print(f"  P{pct}: threshold={threshold:.4f}, flagged={flagged} ({pct_flagged:.1f}%)")
    
    # Use 92nd percentile as default threshold (targets ~8% anomaly rate)
    optimal_threshold = np.percentile(fraud_anomaly_score, 92)
    df["fraud_flag"] = (fraud_anomaly_score >= optimal_threshold).astype(int)
    
    flagged_total = df["fraud_flag"].sum()
    print(f"\n  ✅ Optimal threshold (P92): {optimal_threshold:.4f}")
    print(f"  ✅ Flagged as suspicious: {flagged_total} ({100*flagged_total/len(df):.1f}%)")
    
    # ── 5. Feature contribution analysis ────────────────────
    print("\n📊 Step 5: Feature Contribution Analysis")
    
    # Compare feature distributions: flagged vs normal
    flagged_mask = df["fraud_flag"] == 1
    
    feature_analysis = {}
    for feat in FRAUD_FEATURES:
        normal_mean = float(df.loc[~flagged_mask, feat].mean())
        fraud_mean = float(df.loc[flagged_mask, feat].mean())
        ratio = fraud_mean / max(normal_mean, 0.001)
        feature_analysis[feat] = {
            "normal_mean": round(normal_mean, 4),
            "fraud_mean": round(fraud_mean, 4),
            "fraud_to_normal_ratio": round(ratio, 2),
        }
        print(f"  {feat:30s} Normal={normal_mean:.3f}, Fraud={fraud_mean:.3f}, Ratio={ratio:.2f}x")
    
    # ── 6. Visualization ────────────────────────────────────
    print("\n📊 Step 6: Generating Plots")
    
    # Anomaly score distribution
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Score distribution
    axes[0, 0].hist(fraud_anomaly_score[~flagged_mask], bins=60, alpha=0.7,
                     color="#4CAF50", label="Normal", density=True)
    axes[0, 0].hist(fraud_anomaly_score[flagged_mask], bins=30, alpha=0.7,
                     color="#F44336", label="Flagged", density=True)
    axes[0, 0].axvline(optimal_threshold, color="orange", linestyle="--",
                        linewidth=2, label=f"Threshold ({optimal_threshold:.3f})")
    axes[0, 0].set_xlabel("Fraud Anomaly Score")
    axes[0, 0].set_title("Anomaly Score Distribution", fontweight="bold")
    axes[0, 0].legend()
    
    # GPS Jump vs Claim Frequency
    axes[0, 1].scatter(df.loc[~flagged_mask, "gps_jump_distance"],
                        df.loc[~flagged_mask, "claim_frequency_7day"],
                        alpha=0.3, s=8, color="#4CAF50", label="Normal")
    axes[0, 1].scatter(df.loc[flagged_mask, "gps_jump_distance"],
                        df.loc[flagged_mask, "claim_frequency_7day"],
                        alpha=0.6, s=15, color="#F44336", label="Flagged")
    axes[0, 1].set_xlabel("GPS Jump Distance (km)")
    axes[0, 1].set_ylabel("Claim Frequency (7 day)")
    axes[0, 1].set_title("GPS Jump vs Claims", fontweight="bold")
    axes[0, 1].legend()
    
    # Active Hours vs Cluster Score
    axes[1, 0].scatter(df.loc[~flagged_mask, "active_hours_ratio"],
                        df.loc[~flagged_mask, "nearby_claim_cluster_score"],
                        alpha=0.3, s=8, color="#4CAF50", label="Normal")
    axes[1, 0].scatter(df.loc[flagged_mask, "active_hours_ratio"],
                        df.loc[flagged_mask, "nearby_claim_cluster_score"],
                        alpha=0.6, s=15, color="#F44336", label="Flagged")
    axes[1, 0].set_xlabel("Active Hours Ratio")
    axes[1, 0].set_ylabel("Nearby Claim Cluster Score")
    axes[1, 0].set_title("Activity vs Clustering", fontweight="bold")
    axes[1, 0].legend()
    
    # Feature means comparison
    feat_names = list(feature_analysis.keys())
    normal_means = [feature_analysis[f]["normal_mean"] for f in feat_names]
    fraud_means = [feature_analysis[f]["fraud_mean"] for f in feat_names]
    
    x_pos = np.arange(len(feat_names))
    width = 0.35
    axes[1, 1].bar(x_pos - width/2, normal_means, width, label="Normal", color="#4CAF50", alpha=0.8)
    axes[1, 1].bar(x_pos + width/2, fraud_means, width, label="Flagged", color="#F44336", alpha=0.8)
    axes[1, 1].set_xticks(x_pos)
    axes[1, 1].set_xticklabels([f.replace("_", "\n") for f in feat_names], fontsize=8)
    axes[1, 1].set_title("Feature Means: Normal vs Flagged", fontweight="bold")
    axes[1, 1].legend()
    
    for ax in axes.flat:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    
    plt.suptitle("Fraud Detection — IsolationForest Analysis", fontsize=15, fontweight="bold")
    plt.tight_layout()
    plot_path = REPORTS_DIR / "fraud_detection_analysis.png"
    fig.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  💾 Saved to {plot_path}")
    
    # ── 7. Save model and metadata ──────────────────────────
    model_path = MODELS_DIR / "fraud_iforest.pkl"
    joblib.dump(model, model_path)
    print(f"\n💾 Model saved to {model_path}")
    
    metrics = {
        "contamination": 0.08,
        "optimal_threshold": float(optimal_threshold),
        "threshold_percentile": 92,
        "total_flagged": int(flagged_total),
        "flagged_pct": round(100 * flagged_total / len(df), 2),
        "threshold_analysis": threshold_analysis,
        "feature_analysis": feature_analysis,
        "features": FRAUD_FEATURES,
    }
    
    metrics_path = REPORTS_DIR / "fraud_model_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"💾 Metrics saved to {metrics_path}")
    
    return model, metrics


if __name__ == "__main__":
    train_fraud_model()
