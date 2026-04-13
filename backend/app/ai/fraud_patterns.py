"""
ShieldPay AI — Fraud Pattern Library
=====================================
Defines known fraud patterns and provides matching logic
for the fraud detection pipeline.

Each pattern has:
- A unique ID and name
- Detection criteria
- Severity rating
- Recommended action
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# ─── Known Fraud Patterns ─────────────────────────────────

FRAUD_PATTERNS = {
    "GPS_CLUSTER_SPOOF": {
        "id": "FP-001",
        "name": "GPS Cluster Spoofing",
        "description": "Multiple workers report identical or near-identical GPS coordinates simultaneously, suggesting coordinated location spoofing.",
        "severity": 0.9,
        "signals": ["teleport_detected", "no_accelerometer_data"],
        "min_workers": 3,
        "time_window_hours": 2,
        "action": "FREEZE_AND_INVESTIGATE",
    },
    "TEMPORAL_CLAIM_STACK": {
        "id": "FP-002",
        "name": "Temporal Claim Stacking",
        "description": "Claims filed at exact shift boundary times (start/end), suggesting pre-planned false claims rather than genuine disruption responses.",
        "severity": 0.7,
        "signals": ["claim_spike_detected"],
        "claim_threshold": 3,
        "time_window_hours": 48,
        "action": "FLAG_FOR_REVIEW",
    },
    "DEVICE_ROTATION": {
        "id": "FP-003",
        "name": "Device Rotation",
        "description": "Same worker account accessed from multiple distinct device fingerprints within a short window, suggesting account sharing or spoofing.",
        "severity": 0.75,
        "signals": ["new_install", "emulator_detected"],
        "max_devices": 2,
        "time_window_hours": 48,
        "action": "SOFT_LOCK_AND_VERIFY",
    },
    "WEATHER_MISMATCH": {
        "id": "FP-004",
        "name": "Weather Mismatch Claim",
        "description": "Worker claims weather-related disruption, but environmental data shows no significant weather event in their operating zone.",
        "severity": 0.8,
        "signals": ["low_environmental_match"],
        "env_score_threshold": 0.3,
        "action": "AUTO_REJECT",
    },
    "PHANTOM_DELIVERY": {
        "id": "FP-005",
        "name": "Phantom Delivery Pattern",
        "description": "Worker claims active deliveries but GPS data shows no movement from a single location. Possible idle fraud.",
        "severity": 0.65,
        "signals": ["no_accelerometer_data", "claiming_while_active"],
        "action": "FLAG_FOR_REVIEW",
    },
}


def match_patterns(analysis: Dict) -> List[Dict]:
    """
    Match a fraud analysis result against known fraud patterns.
    Returns a list of matched patterns with confidence scores.
    """
    matches = []
    
    movement = analysis.get("movement", {})
    activity = analysis.get("activity", {})
    environment = analysis.get("environment", {})
    device = analysis.get("device", {})
    graph = analysis.get("graph", {})
    
    # Collect all active signals
    active_signals = set()
    
    if movement.get("teleport_detected"):
        active_signals.add("teleport_detected")
    if not movement.get("accelerometer_consistent", True):
        active_signals.add("no_accelerometer_data")
    if activity.get("claiming_while_active"):
        active_signals.add("claiming_while_active")
    if device.get("is_emulator"):
        active_signals.add("emulator_detected")
    if device.get("flags"):
        active_signals.update(device["flags"])
    if graph.get("claim_spike_detected"):
        active_signals.add("claim_spike_detected")
    
    # Environmental match check
    env_score = environment.get("score", 1.0)
    if env_score < 0.3:
        active_signals.add("low_environmental_match")
    
    # Match against patterns
    for pattern_key, pattern in FRAUD_PATTERNS.items():
        required_signals = set(pattern["signals"])
        overlap = required_signals & active_signals
        
        if len(overlap) > 0:
            # Confidence = fraction of pattern signals that matched
            confidence = len(overlap) / len(required_signals)
            
            # Boost confidence if multiple signals match
            if len(overlap) >= 2:
                confidence = min(1.0, confidence * 1.2)
            
            matches.append({
                "pattern_id": pattern["id"],
                "pattern_name": pattern["name"],
                "description": pattern["description"],
                "matched_signals": list(overlap),
                "total_signals": list(required_signals),
                "confidence": round(confidence, 3),
                "severity": pattern["severity"],
                "recommended_action": pattern["action"],
            })
    
    # Sort by severity * confidence (highest threat first)
    matches.sort(key=lambda m: m["severity"] * m["confidence"], reverse=True)
    
    return matches


def get_cross_signal_score(analysis: Dict) -> float:
    """
    Calculate a cross-signal correlation penalty.
    When multiple independent fraud signals fire simultaneously,
    the combined risk is multiplicatively worse than additive.
    """
    layer_scores = []
    
    movement = analysis.get("movement", {})
    activity = analysis.get("activity", {})
    device = analysis.get("device", {})
    graph = analysis.get("graph", {})
    
    # Collect layer-level safety scores (higher = safer)
    layer_scores.append(movement.get("score", 1.0))
    layer_scores.append(activity.get("score", 1.0))
    layer_scores.append(device.get("score", 1.0))
    layer_scores.append(graph.get("score", 1.0))
    
    if not layer_scores:
        return 1.0  # No data = assume safe
    
    # Count flagged layers (score < 0.5)
    flagged = sum(1 for s in layer_scores if s < 0.5)
    
    if flagged >= 3:
        # Multiplicative penalty: multiple independent signals = very suspicious
        product = 1.0
        for s in layer_scores:
            product *= s
        return round(max(0.0, product), 4)
    elif flagged >= 2:
        # Moderate cross-signal penalty
        avg = sum(layer_scores) / len(layer_scores)
        min_score = min(layer_scores)
        return round((avg + min_score) / 2, 4)  # Weighted toward worst signal
    else:
        # Normal: simple average
        return round(sum(layer_scores) / len(layer_scores), 4)
