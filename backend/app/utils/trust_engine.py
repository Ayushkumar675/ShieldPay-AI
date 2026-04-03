"""
ShieldPay AI — Trust Score Fusion Engine
==========================================
Weighted multi-signal fusion to determine probability of genuine disruption.
"""

import numpy as np

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
