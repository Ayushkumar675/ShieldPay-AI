"""
ShieldPay AI — Trust Score Computation Engine
Composite multi-signal trust verification for claim approval.

claim_approval_probability = weighted(
    real_movement_score       × 0.25,
    delivery_activity_score   × 0.25,
    environmental_match_score × 0.20,
    historical_trust_index    × 0.15,
    fraud_anomaly_score       × 0.15
)
"""
from datetime import datetime
from typing import Dict

from app.models.schemas import TrustScore
from app.ai.fraud_detector import (
    analyze_movement,
    analyze_delivery_activity,
    analyze_environment,
    analyze_device,
    detect_fraud_rings,
    check_and_create_alerts,
)


# Trust score weights
TRUST_WEIGHTS = {
    "movement": 0.25,
    "delivery_activity": 0.25,
    "environmental": 0.20,
    "historical_trust": 0.15,
    "fraud_anomaly": 0.15,
}


async def compute_trust_score(worker_id: str) -> TrustScore:
    """
    Compute comprehensive trust score for a worker.
    Runs all fraud detection layers and produces weighted composite.
    """
    # Run all analysis layers
    movement = await analyze_movement(worker_id)
    activity = await analyze_delivery_activity(worker_id)
    environment = await analyze_environment(worker_id)
    device = await analyze_device(worker_id)
    graph = await detect_fraud_rings(worker_id)

    # Get historical trust from database
    from app.models.database import get_db
    db = get_db()
    worker = await db.users.find_one({"id": worker_id}) if db else None
    historical_trust = worker.get("reliability_score", 0.8) if worker else 0.8

    # Device score affects movement trust
    device_adjusted_movement = movement["score"] * (0.5 + device["score"] * 0.5)

    # Fraud anomaly score (inverted: lower anomaly = higher trust)
    fraud_safety = graph["score"]  # already inverted in detector

    # Compute weighted composite
    composite = (
        device_adjusted_movement * TRUST_WEIGHTS["movement"] +
        activity["score"] * TRUST_WEIGHTS["delivery_activity"] +
        environment["score"] * TRUST_WEIGHTS["environmental"] +
        historical_trust * TRUST_WEIGHTS["historical_trust"] +
        fraud_safety * TRUST_WEIGHTS["fraud_anomaly"]
    )

    # Create fraud alerts if warranted
    analysis = {
        "movement": movement,
        "device": device,
        "graph": graph,
    }
    await check_and_create_alerts(worker_id, analysis)

    trust = TrustScore(
        worker_id=worker_id,
        real_movement_score=round(device_adjusted_movement, 3),
        delivery_activity_score=round(activity["score"], 3),
        environmental_match_score=round(environment["score"], 3),
        historical_trust_index=round(historical_trust, 3),
        fraud_anomaly_score=round(1.0 - fraud_safety, 3),  # Store as fraud probability
        composite_score=round(min(1.0, max(0.0, composite)), 3),
    )

    return trust
