"""
ShieldPay AI — Trust Score Fusion Engine
==========================================
Weighted multi-signal fusion to determine probability of genuine disruption.

trust_score = weighted(
    mobility_stability_index,
    behavioral_trust_index,
    fraud_anomaly_score_inverse,
    environmental_disruption_match
)

Returns 0-1 probability of genuine disruption claim.
"""

import numpy as np
import pandas as pd
import joblib
from pathlib import Path

MODELS_DIR = Path(__file__).parent / "models" / "saved"


# ─── Weights for trust fusion ──────────────────────────────
TRUST_WEIGHTS = {
    "mobility_stability":     0.25,
    "behavioral_trust":       0.25,
    "fraud_inverse":          0.30,  # Heaviest: fraud signal is most critical
    "disruption_match":       0.20,
}


def compute_trust_score(
    mobility_stability_index: float,
    behavioral_trust_index: float,
    fraud_anomaly_score: float,
    disruption_risk_score: float,
) -> dict:
    """
    Compute weighted trust score for a single worker/claim.
    
    Args:
        mobility_stability_index: 0-1, higher = more stable GPS/activity
        behavioral_trust_index: 0-1, higher = more trustworthy behavior
        fraud_anomaly_score: 0-1, higher = MORE suspicious
        disruption_risk_score: 0-1, higher = more environmental disruption
    
    Returns:
        Dict with composite trust score and component breakdown.
    """
    # Invert fraud score: higher fraud_anomaly_score = LOWER trust contribution
    fraud_inverse = 1.0 - fraud_anomaly_score
    
    # Environmental disruption match: if disruption is high AND worker claims loss,
    # it matches expectations → higher trust
    environmental_match = disruption_risk_score
    
    # Weighted composite
    composite = (
        mobility_stability_index * TRUST_WEIGHTS["mobility_stability"] +
        behavioral_trust_index   * TRUST_WEIGHTS["behavioral_trust"] +
        fraud_inverse            * TRUST_WEIGHTS["fraud_inverse"] +
        environmental_match      * TRUST_WEIGHTS["disruption_match"]
    )
    
    # Clamp to [0, 1]
    composite = float(np.clip(composite, 0.0, 1.0))
    
    # Determine action recommendation
    if composite >= 0.75:
        recommendation = "AUTO_APPROVE"
        explanation = "High trust score — genuine disruption pattern detected. Recommend automatic claim approval."
    elif composite >= 0.50:
        recommendation = "MANUAL_REVIEW"
        explanation = "Moderate trust score — some signals uncertain. Recommend manual review before approval."
    elif composite >= 0.30:
        recommendation = "FLAG_SUSPICIOUS"
        explanation = "Low trust score — potential anomaly detected. Flag for fraud investigation."
    else:
        recommendation = "AUTO_REJECT"
        explanation = "Very low trust score — strong fraud indicators. Recommend automatic rejection + investigation."
    
    return {
        "trust_score": round(composite, 4),
        "genuine_disruption_probability": round(composite, 4),
        "recommendation": recommendation,
        "explanation": explanation,
        "component_scores": {
            "mobility_stability": {
                "value": round(float(mobility_stability_index), 4),
                "weight": TRUST_WEIGHTS["mobility_stability"],
                "weighted_contribution": round(
                    float(mobility_stability_index) * TRUST_WEIGHTS["mobility_stability"], 4
                ),
            },
            "behavioral_trust": {
                "value": round(float(behavioral_trust_index), 4),
                "weight": TRUST_WEIGHTS["behavioral_trust"],
                "weighted_contribution": round(
                    float(behavioral_trust_index) * TRUST_WEIGHTS["behavioral_trust"], 4
                ),
            },
            "fraud_safety": {
                "value": round(float(fraud_inverse), 4),
                "weight": TRUST_WEIGHTS["fraud_inverse"],
                "weighted_contribution": round(
                    float(fraud_inverse) * TRUST_WEIGHTS["fraud_inverse"], 4
                ),
            },
            "disruption_match": {
                "value": round(float(environmental_match), 4),
                "weight": TRUST_WEIGHTS["disruption_match"],
                "weighted_contribution": round(
                    float(environmental_match) * TRUST_WEIGHTS["disruption_match"], 4
                ),
            },
        },
    }


def batch_trust_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute trust scores for an entire DataFrame.
    Requires columns: mobility_stability_index, behavioral_trust_index,
                      fraud_anomaly_score, disruption_risk_score_feature
    """
    results = []
    for _, row in df.iterrows():
        result = compute_trust_score(
            mobility_stability_index=row.get("mobility_stability_index", 0.5),
            behavioral_trust_index=row.get("behavioral_trust_index", 0.5),
            fraud_anomaly_score=row.get("fraud_anomaly_score", 0.5),
            disruption_risk_score=row.get("disruption_risk_score_feature", 0.5),
        )
        results.append(result["trust_score"])
    
    df = df.copy()
    df["trust_score"] = results
    return df


if __name__ == "__main__":
    # Example usage
    print("=" * 60)
    print("  ShieldPay AI — Trust Score Fusion Engine")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        ("Genuine worker in flood zone", 0.85, 0.90, 0.10, 0.80),
        ("Suspicious low-activity", 0.30, 0.25, 0.75, 0.20),
        ("Moderate — borderline", 0.60, 0.55, 0.45, 0.50),
        ("Fraud actor with GPS spoof", 0.15, 0.10, 0.95, 0.15),
    ]
    
    for label, msi, bti, fas, drs in test_cases:
        result = compute_trust_score(msi, bti, fas, drs)
        print(f"\n📋 {label}")
        print(f"  Trust Score: {result['trust_score']:.4f}")
        print(f"  Recommendation: {result['recommendation']}")
        print(f"  Explanation: {result['explanation']}")
    
    print(f"\n✅ Trust engine operational")
