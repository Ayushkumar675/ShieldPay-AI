"""
ShieldPay AI — Narrative Intelligence Engine
=============================================
Generates human-readable, contextual explanations for every
risk score, payout decision, fraud flag, and forecast in the system.

This transforms raw numbers into meaningful stories that help
workers understand their protection and admins understand their platform.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import hashlib


# ─── Risk Narratives ──────────────────────────────────────

def generate_risk_narrative(risk_data: Dict, city: str = "", worker_name: str = "") -> str:
    """Generate a human-readable risk narrative for a worker's current situation."""
    composite = risk_data.get("composite_risk", 0)
    factors = risk_data.get("factors", {})
    
    weather = factors.get("weather", {})
    traffic = factors.get("traffic", {})
    seasonal = factors.get("seasonal", {})
    
    # Build contextual sentences
    parts = []
    
    # Weather context
    weather_score = weather.get("score", 0)
    condition = weather.get("condition", "unknown")
    rainfall = weather.get("rainfall_mm", 0)
    if weather_score > 0.6:
        condition_text = condition.replace("_", " ")
        if rainfall > 0:
            parts.append(f"{city or 'Your area'} is experiencing {condition_text} conditions with {rainfall}mm rainfall")
        else:
            parts.append(f"{city or 'Your area'} is under {condition_text} conditions")
    elif weather_score > 0.3:
        parts.append(f"Weather in {city or 'your area'} shows moderate disruption potential")
    
    # Traffic context
    traffic_score = traffic.get("score", 0)
    avg_speed = traffic.get("avg_speed_kmh", 20)
    if traffic_score > 0.7:
        parts.append(f"traffic congestion is severe (avg {avg_speed}km/h)")
    elif traffic_score > 0.4:
        parts.append(f"traffic is moderately congested")
    
    # Seasonal context
    season = seasonal.get("season", "")
    seasonal_score = seasonal.get("score", 0)
    if seasonal_score > 0.6:
        season_names = {
            "monsoon": "monsoon season",
            "summer": "peak summer heat",
            "winter": "winter conditions",
            "post_monsoon_festival": "post-monsoon festival season"
        }
        parts.append(f"seasonal patterns ({season_names.get(season, season)}) are adding to the risk")

    # Compose
    if not parts:
        return f"Current conditions in {city or 'your area'} are stable. Your delivery zone faces minimal disruption risk ({(composite * 100):.0f}%)."
    
    narrative = ". ".join(parts[:2]).capitalize()
    narrative += f". Combined, your delivery zone faces a {(composite * 100):.0f}% disruption risk"
    
    if composite > 0.7:
        narrative += " — consider adjusting your schedule to protect your income."
    elif composite > 0.4:
        narrative += " — stay alert to changing conditions."
    else:
        narrative += "."
    
    return narrative


# ─── Claim Decision Narratives ────────────────────────────

def generate_claim_narrative(claim_data: Dict) -> str:
    """Generate a human-readable explanation of why a claim was approved/denied."""
    status = claim_data.get("status", "pending")
    trust_score = claim_data.get("trust_score", {})
    composite = trust_score.get("composite_score", 0) if isinstance(trust_score, dict) else 0
    payout_tier = claim_data.get("payout_tier", "delayed")
    payout_amount = claim_data.get("payout_amount", 0)
    disruption_type = claim_data.get("disruption_type", "weather")
    
    disruption_labels = {
        "weather": "weather disruption",
        "warehouse_shutdown": "warehouse shutdown",
        "curfew_lockdown": "curfew lockdown",
        "traffic_gridlock": "traffic gridlock",
        "parcel_allocation_drop": "parcel allocation drop"
    }
    disruption_text = disruption_labels.get(disruption_type, "disruption event")
    
    if status in ("auto_approved", "paid"):
        narrative = f"Your claim was automatically approved due to a verified {disruption_text}. "
        narrative += f"Your trust score ({(composite * 100):.0f}%) exceeds the instant payout threshold. "
        if payout_amount > 0:
            narrative += f"₹{payout_amount:,.0f} has been disbursed to your account."
        return narrative
    
    elif status == "soft_verify":
        narrative = f"A {disruption_text} has been detected in your zone. "
        narrative += f"Your trust score ({(composite * 100):.0f}%) qualifies for quick verification. "
        narrative += "Please confirm the claim in your dashboard to release the payout."
        return narrative
    
    elif status == "delayed_review":
        narrative = f"A {disruption_text} has been detected. "
        narrative += f"Your current trust score ({(composite * 100):.0f}%) requires manual review before disbursement. "
        narrative += "An admin will review your claim within 24-48 hours. Continue maintaining good delivery patterns to improve your trust score."
        return narrative
    
    elif status == "rejected":
        narrative = f"Your claim related to a {disruption_text} could not be verified. "
        narrative += "The AI detected inconsistencies between the reported disruption and your activity data. "
        narrative += "If you believe this is an error, contact support."
        return narrative
    
    return f"Your claim is currently {status}. We're processing it through our AI verification pipeline."


# ─── Trust Score Narratives ───────────────────────────────

def generate_trust_narrative(trust_data: Dict, worker_name: str = "") -> str:
    """Generate a personalized trust score explanation."""
    composite = trust_data.get("composite_score", 0)
    
    greeting = f"Hi {worker_name}! " if worker_name else ""
    
    if composite >= 0.85:
        narrative = f"{greeting}Your trust score is excellent at {(composite * 100):.0f}%. "
        narrative += "You're in the Instant Payout tier — any valid claims will be processed and paid automatically within seconds. "
        narrative += "Keep up the consistent delivery performance!"
        return narrative
    
    elif composite >= 0.70:
        narrative = f"{greeting}Your trust score is strong at {(composite * 100):.0f}%. "
        narrative += "You're close to the Instant Payout tier (85%). "
        gap = 0.85 - composite
        narrative += f"Just {(gap * 100):.0f}% more to unlock automatic payouts. "
        narrative += "Maintain regular deliveries and avoid claim spikes to get there."
        return narrative
    
    elif composite >= 0.50:
        narrative = f"{greeting}Your trust score is {(composite * 100):.0f}%. "
        narrative += "Claims require quick verification — just a simple confirmation from you. "
        narrative += "To improve: maintain consistent delivery routes, keep your identity verified, and avoid unusual activity patterns."
        return narrative
    
    else:
        narrative = f"{greeting}Your trust score is currently {(composite * 100):.0f}%. "
        narrative += "Claims will require manual admin review (24-48 hours). "
        narrative += "Focus on completing deliveries consistently, and your score will recover over the next 2-3 weeks."
        return narrative


# ─── Worker Advice Narrative ──────────────────────────────

def generate_weekly_advice(forecast_data: Dict, risk_data: Dict = None) -> str:
    """Generate actionable weekly advice for a worker."""
    risk_forecast = forecast_data.get("risk_forecast", [])
    income_forecast = forecast_data.get("income_forecast", [])
    
    advice_parts = []
    
    # Find the riskiest day
    if risk_forecast:
        max_risk_day = max(risk_forecast, key=lambda d: d.get("risk", 0))
        max_risk = max_risk_day.get("risk", 0)
        max_risk_name = max_risk_day.get("day", "Unknown")
        
        if max_risk > 0.7:
            advice_parts.append(
                f"⚠️ {max_risk_name}'s risk forecast is elevated at {(max_risk * 100):.0f}%. "
                f"Consider scheduling fewer deliveries or planning alternative routes."
            )
        elif max_risk > 0.4:
            advice_parts.append(
                f"📊 {max_risk_name} shows moderate risk ({(max_risk * 100):.0f}%). Stay alert to changing conditions."
            )
    
    # Income projection
    if income_forecast:
        total_predicted = sum(w.get("predicted", 0) for w in income_forecast)
        total_normal = sum(w.get("normal", 0) for w in income_forecast)
        if total_normal > 0:
            loss_pct = ((total_normal - total_predicted) / total_normal) * 100
            if loss_pct > 15:
                advice_parts.append(
                    f"💰 Your projected income is {loss_pct:.0f}% below normal this month. "
                    f"Your insurance coverage protects against disruption-related losses."
                )
            elif loss_pct < 5:
                advice_parts.append(
                    "✅ Your income forecast looks stable this month. Keep up the great work!"
                )
    
    if not advice_parts:
        advice_parts.append("🌤 Conditions look favorable. No major disruptions are predicted for your zone.")
    
    return " ".join(advice_parts)


# ─── Admin Platform Summary ──────────────────────────────

def generate_admin_weekly_summary(
    total_claims: int,
    total_payout: float,
    auto_approved: int,
    manual_review: int,
    fraud_alerts: int,
    fraud_rings: int,
    liquidity_ratio: float,
    reserve_balance: float,
) -> str:
    """Generate an intelligent weekly summary for platform admins."""
    parts = []
    
    # Claims overview
    if total_claims > 0:
        approval_rate = (auto_approved / total_claims * 100) if total_claims > 0 else 0
        parts.append(
            f"This period: {total_claims} claims processed, ₹{total_payout:,.0f} disbursed "
            f"({approval_rate:.0f}% auto-approved)."
        )
    else:
        parts.append("No claims have been processed this period.")
    
    # Fraud status
    if fraud_rings > 0:
        parts.append(f"🕸 {fraud_rings} fraud ring(s) detected and flagged for investigation.")
    if fraud_alerts > 10:
        parts.append(f"⚠️ Elevated fraud activity: {fraud_alerts} alerts triggered.")
    elif fraud_alerts > 0:
        parts.append(f"🛡 {fraud_alerts} fraud alerts — within normal range.")
    else:
        parts.append("🛡 Zero fraud alerts — platform integrity is strong.")
    
    # Financial health
    if liquidity_ratio >= 2.0:
        health = "excellent"
    elif liquidity_ratio >= 1.5:
        health = "healthy"
    elif liquidity_ratio >= 1.0:
        health = "adequate"
    else:
        health = "critical — immediate attention required"
    
    parts.append(
        f"Platform financial health: {health} (liquidity ratio: {liquidity_ratio:.1f}x, "
        f"reserve: ₹{reserve_balance:,.0f})."
    )
    
    # Recommendation
    if manual_review > auto_approved and total_claims > 5:
        parts.append(
            "💡 Recommendation: High manual review rate suggests trust scores may need recalibration, "
            "or a new fraud pattern is emerging."
        )
    
    return " ".join(parts)


# ─── Anomaly Spotlight ────────────────────────────────────

def generate_anomaly_spotlight(
    liquidity_ratio: float,
    fraud_alerts: int,
    payout_rate: float,
    claim_spike: bool = False,
) -> Optional[Dict]:
    """Identify the single most concerning metric and return a spotlight alert."""
    concerns = []
    
    if liquidity_ratio < 1.2:
        concerns.append({
            "metric": "Liquidity Ratio",
            "value": f"{liquidity_ratio:.1f}x",
            "severity": "critical" if liquidity_ratio < 1.0 else "warning",
            "message": f"Reserve ratio has dropped to {liquidity_ratio:.1f}x — "
                      f"{'below safety threshold. Consider pausing payouts.' if liquidity_ratio < 1.0 else 'approaching the safety threshold. Monitor closely.'}",
        })
    
    if fraud_alerts > 20:
        concerns.append({
            "metric": "Fraud Alerts",
            "value": str(fraud_alerts),
            "severity": "critical" if fraud_alerts > 40 else "warning",
            "message": f"Unusual fraud activity: {fraud_alerts} alerts in the current period. "
                      f"Investigate potential coordinated attack.",
        })
    
    if claim_spike:
        concerns.append({
            "metric": "Claim Volume",
            "value": "Spike Detected",
            "severity": "warning",
            "message": "Claim volume has spiked beyond 3x the normal rate. "
                      "Payout throttling may be activated automatically.",
        })
    
    if not concerns:
        return {
            "metric": "All Clear",
            "value": "✓",
            "severity": "normal",
            "message": "All platform metrics are within normal operating parameters. No anomalies detected.",
        }
    
    # Return the highest severity concern
    severity_order = {"critical": 0, "warning": 1, "normal": 2}
    concerns.sort(key=lambda c: severity_order.get(c["severity"], 2))
    return concerns[0]


# ─── Fraud Explanation Narratives ─────────────────────────

def generate_fraud_explanation(analysis: Dict) -> str:
    """Generate a cross-signal fraud analysis explanation."""
    parts = []
    
    movement = analysis.get("movement", {})
    activity = analysis.get("activity", {})
    environment = analysis.get("environment", {})
    device = analysis.get("device", {})
    graph = analysis.get("graph", {})
    
    if movement.get("teleport_detected"):
        parts.append("GPS location teleport anomaly detected — sudden location jump exceeding normal travel speed")
    
    if not movement.get("accelerometer_consistent", True):
        parts.append("no accelerometer data available — device may be stationary or spoofed")
    
    if activity.get("claiming_while_active"):
        parts.append("worker filed a disruption claim while actively completing deliveries")
    
    if device.get("is_emulator"):
        parts.append("application running on emulated device environment")
    
    if device.get("is_rooted"):
        parts.append("rooted/jailbroken device detected — increased spoofing risk")
    
    if graph.get("in_fraud_ring"):
        ring_id = graph.get("ring_id", "unknown")
        parts.append(f"worker is associated with fraud ring {ring_id}")
    
    if graph.get("claim_spike_detected"):
        count = graph.get("recent_claims_48h", 0)
        parts.append(f"unusual claim frequency: {count} claims in 48 hours")
    
    if not parts:
        return "No significant fraud indicators detected. All signals within normal parameters."
    
    # Cross-signal amplification note
    flagged_layers = sum(1 for x in [
        movement.get("teleport_detected"),
        activity.get("claiming_while_active"),
        device.get("is_emulator") or device.get("is_rooted"),
        graph.get("in_fraud_ring"),
    ] if x)
    
    narrative = "Detected anomalies: " + "; ".join(parts) + "."
    
    if flagged_layers >= 3:
        narrative += " ⚠️ CRITICAL: Multiple independent fraud signals are corroborating — high-confidence fraud pattern."
    elif flagged_layers >= 2:
        narrative += " Cross-signal correlation detected — investigation recommended."
    
    return narrative
