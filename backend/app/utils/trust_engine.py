"""
ShieldPay AI — Trust Score Fusion Engine (Adaptive)
====================================================
Self-learning weighted multi-signal fusion with:
  • Temporal trust decay for inactive workers
  • Behavioral momentum for consistent performers
  • Dynamic weight adjustment based on worker history
  • Human-readable explanation chain
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional


# ─── Base Weights (adapted dynamically per worker) ─────────
BASE_TRUST_WEIGHTS = {
    "mobility_stability":     0.25,
    "behavioral_trust":       0.25,
    "fraud_inverse":          0.30,
    "disruption_match":       0.20,
}

# ─── Temporal Decay Configuration ─────────────────────────
DECAY_HALF_LIFE_DAYS = 30     # Trust halves every 30 days of inactivity
MIN_TRUST_FLOOR = 0.40        # Trust never decays below this
MOMENTUM_BONUS_CAP = 0.08     # Max trust boost from behavioral momentum


def compute_adaptive_weights(
    claim_history: Dict = None,
) -> Dict[str, float]:
    """
    Dynamically adjust trust weights based on worker's claim history.
    Workers with prior fraud flags get heavier fraud_inverse weighting.
    Workers with consistent clean history get more mobility/behavioral weight.
    """
    weights = dict(BASE_TRUST_WEIGHTS)
    
    if claim_history is None:
        return weights
    
    flagged_claims = claim_history.get("flagged", 0)
    rejected_claims = claim_history.get("rejected", 0)
    total_claims = claim_history.get("total", 0)
    
    # If worker has had suspicious history, increase fraud scrutiny
    if rejected_claims > 0 or flagged_claims > 2:
        fraud_boost = min(0.10, (rejected_claims * 0.04 + flagged_claims * 0.02))
        weights["fraud_inverse"] += fraud_boost
        # Redistribute from other weights proportionally
        redistribution = fraud_boost / 3
        weights["mobility_stability"] -= redistribution
        weights["behavioral_trust"] -= redistribution
        weights["disruption_match"] -= redistribution
    
    # If worker has a clean, long history, reward behavioral trust
    elif total_claims > 5 and flagged_claims == 0 and rejected_claims == 0:
        behavioral_boost = min(0.05, total_claims * 0.005)
        weights["behavioral_trust"] += behavioral_boost
        weights["fraud_inverse"] -= behavioral_boost
    
    # Ensure weights sum to 1.0
    total = sum(weights.values())
    weights = {k: round(v / total, 4) for k, v in weights.items()}
    
    return weights


def compute_temporal_decay(
    base_score: float,
    last_activity_date: Optional[datetime] = None,
) -> float:
    """
    Apply temporal decay to a trust score based on inactivity.
    Workers who haven't been active gradually lose trust.
    """
    if last_activity_date is None:
        return base_score  # No activity data → no decay
    
    days_inactive = (datetime.utcnow() - last_activity_date).days
    
    if days_inactive <= 3:
        return base_score  # Grace period: no decay for first 3 days
    
    # Exponential decay with half-life
    decay_factor = 0.5 ** (days_inactive / DECAY_HALF_LIFE_DAYS)
    decayed = base_score * decay_factor
    
    return max(MIN_TRUST_FLOOR, decayed)


def compute_behavioral_momentum(
    recent_deliveries: int = 0,
    streak_days: int = 0,
) -> float:
    """
    Calculate a trust bonus for workers with consistent good behavior.
    Rewards regular delivery activity over time.
    """
    if streak_days <= 0 or recent_deliveries <= 0:
        return 0.0
    
    # Bonus scales with streak length and delivery volume
    streak_bonus = min(streak_days / 30, 1.0) * 0.04  # Max 0.04 from streaks
    volume_bonus = min(recent_deliveries / 100, 1.0) * 0.04  # Max 0.04 from volume
    
    return min(MOMENTUM_BONUS_CAP, streak_bonus + volume_bonus)


def compute_trust_score(
    mobility_stability_index: float,
    behavioral_trust_index: float,
    fraud_anomaly_score: float,
    disruption_risk_score: float,
    claim_history: Dict = None,
    last_activity_date: Optional[datetime] = None,
    recent_deliveries: int = 0,
    streak_days: int = 0,
) -> dict:
    """
    Compute adaptive weighted trust score for a single worker/claim.
    
    Enhancements over v1:
    - Dynamic weight adjustment based on claim history
    - Temporal decay for inactive workers
    - Behavioral momentum bonus for consistent performers
    - Explanation chain documenting every factor
    """
    # Get adaptive weights
    weights = compute_adaptive_weights(claim_history)
    
    # Invert fraud score: higher fraud_anomaly_score = LOWER trust
    fraud_inverse = 1.0 - fraud_anomaly_score
    
    # Environmental disruption match
    environmental_match = disruption_risk_score
    
    # Weighted composite
    composite = (
        mobility_stability_index * weights["mobility_stability"] +
        behavioral_trust_index   * weights["behavioral_trust"] +
        fraud_inverse            * weights["fraud_inverse"] +
        environmental_match      * weights["disruption_match"]
    )
    
    # Apply temporal decay
    pre_decay = composite
    composite = compute_temporal_decay(composite, last_activity_date)
    decay_applied = pre_decay != composite
    
    # Apply behavioral momentum bonus
    momentum = compute_behavioral_momentum(recent_deliveries, streak_days)
    composite = min(1.0, composite + momentum)
    
    # Clamp to [0, 1]
    composite = float(np.clip(composite, 0.0, 1.0))
    
    # Determine action recommendation
    if composite >= 0.85:
        recommendation = "AUTO_APPROVE"
        explanation = "Excellent trust — genuine disruption pattern verified. Automatic claim approval recommended."
    elif composite >= 0.70:
        recommendation = "AUTO_APPROVE"
        explanation = "Strong trust score with verified activity patterns. Automatic approval recommended."
    elif composite >= 0.50:
        recommendation = "MANUAL_REVIEW"
        explanation = "Moderate trust — some signals require verification. Quick confirmation recommended."
    elif composite >= 0.30:
        recommendation = "FLAG_SUSPICIOUS"
        explanation = "Low trust — potential anomaly detected. Investigation recommended before approval."
    else:
        recommendation = "AUTO_REJECT"
        explanation = "Very low trust — strong fraud indicators present. Automatic rejection recommended."
    
    # Build explanation chain
    explanation_chain = []
    explanation_chain.append(
        f"Base mobility stability: {mobility_stability_index:.2f} (weight: {weights['mobility_stability']:.2f})"
    )
    explanation_chain.append(
        f"Behavioral trust index: {behavioral_trust_index:.2f} (weight: {weights['behavioral_trust']:.2f})"
    )
    explanation_chain.append(
        f"Fraud safety (inverted): {fraud_inverse:.2f} (weight: {weights['fraud_inverse']:.2f})"
    )
    explanation_chain.append(
        f"Environmental match: {environmental_match:.2f} (weight: {weights['disruption_match']:.2f})"
    )
    
    if decay_applied:
        explanation_chain.append(
            f"⚠ Temporal decay applied: score reduced from {pre_decay:.2f} due to inactivity"
        )
    
    if momentum > 0:
        explanation_chain.append(
            f"✅ Behavioral momentum bonus: +{momentum:.3f} from {streak_days}-day streak ({recent_deliveries} recent deliveries)"
        )
    
    if claim_history and (claim_history.get("rejected", 0) > 0 or claim_history.get("flagged", 0) > 2):
        explanation_chain.append(
            f"⚠ Elevated fraud scrutiny: {claim_history.get('rejected', 0)} rejections, {claim_history.get('flagged', 0)} flags in history"
        )
    
    explanation_chain.append(f"Final composite: {composite:.4f} → {recommendation}")
    
    return {
        "trust_score": round(composite, 4),
        "genuine_disruption_probability": round(composite, 4),
        "recommendation": recommendation,
        "explanation": explanation,
        "explanation_chain": explanation_chain,
        "adaptive_weights": weights,
        "modifiers": {
            "temporal_decay_applied": decay_applied,
            "momentum_bonus": round(momentum, 4),
            "pre_decay_score": round(pre_decay, 4),
        },
        "component_scores": {
            "mobility_stability": {
                "value": round(float(mobility_stability_index), 4),
                "weight": weights["mobility_stability"],
                "weighted_contribution": round(
                    float(mobility_stability_index) * weights["mobility_stability"], 4
                ),
            },
            "behavioral_trust": {
                "value": round(float(behavioral_trust_index), 4),
                "weight": weights["behavioral_trust"],
                "weighted_contribution": round(
                    float(behavioral_trust_index) * weights["behavioral_trust"], 4
                ),
            },
            "fraud_safety": {
                "value": round(float(fraud_inverse), 4),
                "weight": weights["fraud_inverse"],
                "weighted_contribution": round(
                    float(fraud_inverse) * weights["fraud_inverse"], 4
                ),
            },
            "disruption_match": {
                "value": round(float(environmental_match), 4),
                "weight": weights["disruption_match"],
                "weighted_contribution": round(
                    float(environmental_match) * weights["disruption_match"], 4
                ),
            },
        },
    }
