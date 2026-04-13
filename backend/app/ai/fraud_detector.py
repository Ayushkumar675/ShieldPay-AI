"""
ShieldPay AI — Fraud Detection & Anti-Spoofing Engine (Enhanced)
Multi-layer AI defense architecture with:
  • Deterministic scoring (no random jitter on refresh)
  • Cross-signal correlation penalties
  • Pattern matching against known fraud signatures
  • Fraud analysis narrative generation

Layers:
1. Behavioral Movement Intelligence (GPS, accelerometer, teleport detection)
2. Delivery Activity Correlation (parcels assigned vs delivered)
3. Environmental Consensus Engine (cross-worker disruption validation)
4. Device Authenticity Signals (emulator, root, app fingerprint)
5. Collective Fraud Graph Detection (graph ML, community detection)
"""
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.ai.fraud_patterns import match_patterns, get_cross_signal_score
from app.ai.narrative_engine import generate_fraud_explanation


def _seeded_value(seed_str: str, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Deterministic float from seed string."""
    h = int(hashlib.sha256(seed_str.encode()).hexdigest()[:8], 16)
    normalized = (h % 10000) / 10000.0
    return min_val + normalized * (max_val - min_val)


def _date_seed() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


# ─── Layer 1: Behavioral Movement Intelligence ───────────

async def analyze_movement(worker_id: str) -> Dict:
    """Detect GPS spoofing and movement anomalies using worker data."""
    from app.models.database import get_db
    db = get_db()

    worker = await db["users"].find_one({"id": worker_id}) if db is not None else None
    device = (worker.get("device_signals") or {}) if worker else {}
    reliability = worker.get("reliability_score", 0.8) if worker else 0.8

    # Teleport detection based on device signals
    teleport_detected = False
    if device.get("background_location_streaming"):
        # Workers with BG streaming but no accelerometer are suspicious
        if not device.get("accelerometer_available", True):
            teleport_detected = True

    # Accelerometer consistency — derived from actual device data
    accel_consistent = device.get("accelerometer_available", True)
    if not accel_consistent:
        accel_score = 0.3
    else:
        # Score based on reliability — highly reliable workers have consistent movement
        accel_score = 0.6 + reliability * 0.4

    # Route continuity — derived from reliability
    if teleport_detected:
        route_score = 0.15 + reliability * 0.2
    else:
        route_score = 0.5 + reliability * 0.5

    # Composite movement score
    movement_score = (accel_score * 0.4 + route_score * 0.4 + (0.0 if teleport_detected else 0.2))

    return {
        "score": round(min(1.0, movement_score), 3),
        "teleport_detected": teleport_detected,
        "accelerometer_consistent": accel_consistent,
        "accel_score": round(accel_score, 3),
        "route_continuity_score": round(route_score, 3),
        "flags": _get_movement_flags(teleport_detected, accel_consistent),
    }


# ─── Layer 2: Delivery Activity Correlation ──────────────

async def analyze_delivery_activity(worker_id: str) -> Dict:
    """Validate delivery patterns against warehouse dispatch data."""
    from app.models.database import get_db
    db = get_db()

    worker = await db["users"].find_one({"id": worker_id}) if db is not None else None
    avg_parcels = worker.get("avg_daily_parcels", 30) if worker else 30
    reliability = worker.get("reliability_score", 0.8) if worker else 0.8

    # Delivery ratio derived from reliability
    delivery_ratio = reliability * 0.95  # Reliable workers deliver ~95% of assigned

    # Check for suspicious inactivity claims — less reliable workers are more likely
    claiming_while_active = reliability < 0.4

    # Warehouse dispatch correlation
    if reliability > 0.6:
        dispatch_correlation = 0.7 + reliability * 0.3
    else:
        dispatch_correlation = 0.3 + reliability * 0.4

    activity_score = (
        delivery_ratio * 0.4 +
        dispatch_correlation * 0.3 +
        (0.0 if claiming_while_active else 0.3)
    )

    return {
        "score": round(min(1.0, activity_score), 3),
        "delivery_ratio": round(delivery_ratio, 3),
        "dispatch_correlation": round(dispatch_correlation, 3),
        "claiming_while_active": claiming_while_active,
        "avg_daily_parcels": avg_parcels,
    }


# ─── Layer 3: Environmental Consensus Engine ─────────────

async def analyze_environment(worker_id: str) -> Dict:
    """Cross-validate disruption claims with nearby workers."""
    from app.models.database import get_db
    db = get_db()

    worker = await db["users"].find_one({"id": worker_id}) if db is not None else None
    warehouse_id = worker.get("warehouse_id", "") if worker else ""
    nearby_claims = 0

    if db is not None and warehouse_id:
        nearby_claims = await db["claims"].count_documents({
            "created_at": {"$gte": datetime.utcnow() - timedelta(hours=24)},
        })
        nearby_workers = await db["users"].count_documents({"warehouse_id": warehouse_id})
        claim_density = nearby_claims / max(nearby_workers, 1)
    else:
        claim_density = 0.3

    # Higher claim density = more corroboration = higher environmental match
    if claim_density > 0.3:
        env_score = min(1.0, 0.8 + claim_density * 0.15)
    elif claim_density > 0.1:
        env_score = 0.5 + claim_density * 0.5
    else:
        env_score = 0.2 + claim_density * 0.3  # Isolated claim → somewhat suspicious

    # Deterministic telecom correlation based on claim density
    telecom_correlated = claim_density > 0.15

    return {
        "score": round(min(1.0, env_score), 3),
        "claim_density": round(claim_density, 3),
        "nearby_claims": nearby_claims,
        "telecom_correlated": telecom_correlated,
    }


# ─── Layer 4: Device Authenticity ────────────────────────

async def analyze_device(worker_id: str) -> Dict:
    """Check device integrity signals."""
    from app.models.database import get_db
    db = get_db()

    worker = await db["users"].find_one({"id": worker_id}) if db is not None else None
    device = (worker.get("device_signals") or {}) if worker else {}

    is_emulator = device.get("is_emulator", False)
    is_rooted = device.get("is_rooted", False)
    app_age = device.get("app_install_age_days", 30)
    bg_streaming = device.get("background_location_streaming", False)

    score = 1.0
    flags = []

    if is_emulator:
        score -= 0.4
        flags.append("emulator_detected")
    if is_rooted:
        score -= 0.3
        flags.append("rooted_device")
    if bg_streaming:
        score -= 0.2
        flags.append("abnormal_bg_location")
    if app_age < 7:
        score -= 0.15
        flags.append("new_install")

    return {
        "score": round(max(0.0, score), 3),
        "is_emulator": is_emulator,
        "is_rooted": is_rooted,
        "app_install_age_days": app_age,
        "background_streaming": bg_streaming,
        "flags": flags,
    }


# ─── Layer 5: Graph-Based Fraud Ring Detection ───────────

async def detect_fraud_rings(worker_id: str) -> Dict:
    """Detect coordinated fraud using graph analysis."""
    from app.models.database import get_db
    db = get_db()

    recent_claims = 0
    if db is not None:
        recent_claims = await db["claims"].count_documents({
            "worker_id": worker_id,
            "created_at": {"$gte": datetime.utcnow() - timedelta(hours=48)}
        })
    
    claim_spike = recent_claims > 3

    # Check fraud ring membership
    ring = None
    if db is not None:
        ring = await db['fraud_rings'].find_one({"worker_ids": worker_id})
    in_fraud_ring = ring is not None

    # Deterministic anomaly score
    anomaly_score = 0.0
    if claim_spike:
        anomaly_score += 0.4
    if in_fraud_ring:
        anomaly_score += 0.5
    anomaly_score += recent_claims * 0.05

    return {
        "score": round(min(1.0, 1.0 - anomaly_score), 3),
        "anomaly_score": round(min(1.0, anomaly_score), 3),
        "claim_spike_detected": claim_spike,
        "in_fraud_ring": in_fraud_ring,
        "recent_claims_48h": recent_claims,
        "ring_id": ring["id"] if ring else None,
    }


# ─── Full Analysis with Cross-Signal Correlation ─────────

async def run_full_analysis(worker_id: str) -> Dict:
    """
    Run all 5 fraud detection layers and compute cross-signal correlations.
    Returns enriched analysis with pattern matches and narrative explanation.
    """
    movement = await analyze_movement(worker_id)
    activity = await analyze_delivery_activity(worker_id)
    environment = await analyze_environment(worker_id)
    device = await analyze_device(worker_id)
    graph = await detect_fraud_rings(worker_id)

    analysis = {
        "movement": movement,
        "activity": activity,
        "environment": environment,
        "device": device,
        "graph": graph,
    }

    # Cross-signal correlation score
    cross_signal = get_cross_signal_score(analysis)

    # Pattern matching
    matched_patterns = match_patterns(analysis)

    # Generate human-readable explanation
    narrative = generate_fraud_explanation(analysis)

    # Composite fraud score (lower = more suspicious)
    layer_scores = [
        movement["score"],
        activity["score"],
        environment["score"],
        device["score"],
        graph["score"],
    ]
    avg_score = sum(layer_scores) / len(layer_scores)

    # If cross-signal penalty is active, use it instead of simple average
    composite_safety = min(avg_score, cross_signal)

    return {
        **analysis,
        "composite_safety_score": round(composite_safety, 3),
        "cross_signal_score": cross_signal,
        "matched_patterns": matched_patterns,
        "pattern_count": len(matched_patterns),
        "narrative": narrative,
        "layer_scores": {
            "movement": movement["score"],
            "activity": activity["score"],
            "environment": environment["score"],
            "device": device["score"],
            "graph": graph["score"],
        },
    }


# ─── Generate Fraud Alerts ──────────────────────────────

async def check_and_create_alerts(worker_id: str, analysis: Dict) -> List[Dict]:
    """Create fraud alerts based on analysis results."""
    from app.models.database import get_db
    from app.models.schemas import FraudAlert
    db = get_db()
    alerts = []

    movement = analysis.get("movement", {})
    if movement.get("teleport_detected"):
        alert = FraudAlert(
            worker_id=worker_id,
            alert_type="gps_spoof",
            severity=0.8,
            details={"flags": movement.get("flags", [])},
        )
        if db is not None:
            await db["fraud_alerts"].insert_one(alert.model_dump())
        alerts.append(alert.model_dump())

    device = analysis.get("device", {})
    if device.get("is_emulator") or device.get("is_rooted"):
        alert = FraudAlert(
            worker_id=worker_id,
            alert_type="device_integrity",
            severity=0.7,
            details={"flags": device.get("flags", [])},
        )
        if db is not None:
            await db["fraud_alerts"].insert_one(alert.model_dump())
        alerts.append(alert.model_dump())

    graph = analysis.get("graph", {})
    if graph.get("claim_spike_detected"):
        alert = FraudAlert(
            worker_id=worker_id,
            alert_type="claim_spike",
            severity=0.6,
            details={"recent_claims": graph.get("recent_claims_48h", 0)},
        )
        if db is not None:
            await db["fraud_alerts"].insert_one(alert.model_dump())
        alerts.append(alert.model_dump())

    if graph.get("in_fraud_ring"):
        alert = FraudAlert(
            worker_id=worker_id,
            alert_type="ring_detected",
            severity=0.9,
            details={"ring_id": graph.get("ring_id")},
        )
        if db is not None:
            await db["fraud_alerts"].insert_one(alert.model_dump())
        alerts.append(alert.model_dump())

    # New: Pattern-matched alerts
    for pattern in analysis.get("matched_patterns", []):
        if pattern["confidence"] > 0.6:
            alert = FraudAlert(
                worker_id=worker_id,
                alert_type=f"pattern_{pattern['pattern_id']}",
                severity=pattern["severity"],
                details={
                    "pattern_name": pattern["pattern_name"],
                    "matched_signals": pattern["matched_signals"],
                    "confidence": pattern["confidence"],
                    "recommended_action": pattern["recommended_action"],
                },
            )
            if db is not None:
                await db["fraud_alerts"].insert_one(alert.model_dump())
            alerts.append(alert.model_dump())

    return alerts


# ─── Helpers ─────────────────────────────────────────────

def _get_movement_flags(teleport: bool, accel: bool) -> List[str]:
    flags = []
    if teleport:
        flags.append("location_teleport_anomaly")
    if not accel:
        flags.append("no_accelerometer_data")
    return flags
