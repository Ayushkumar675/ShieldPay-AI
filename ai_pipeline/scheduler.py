"""
ShieldPay AI — Parametric Automation Scheduler
=================================================
Background job that simulates the full parametric insurance pipeline:

1. Simulate weather disruption feed
2. Run risk prediction model
3. Check trust score
4. Auto-generate claim event if thresholds met
5. Log decision reasoning

Runs as an async background task alongside the API server.
"""

import asyncio
import json
import numpy as np
import joblib
from datetime import datetime
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models" / "saved"
LOGS_DIR = BASE_DIR / "logs"


# ─── Weather Simulation ────────────────────────────────────

CITY_WEATHER_PROFILES = {
    "Mumbai": {"rain_base": 85, "flood_prob": 0.40, "traffic_base": 0.80},
    "Delhi": {"rain_base": 25, "flood_prob": 0.10, "traffic_base": 0.75},
    "Bangalore": {"rain_base": 55, "flood_prob": 0.15, "traffic_base": 0.85},
    "Chennai": {"rain_base": 70, "flood_prob": 0.35, "traffic_base": 0.65},
    "Kolkata": {"rain_base": 75, "flood_prob": 0.30, "traffic_base": 0.70},
    "Pune": {"rain_base": 40, "flood_prob": 0.12, "traffic_base": 0.55},
    "Hyderabad": {"rain_base": 45, "flood_prob": 0.18, "traffic_base": 0.60},
    "Ahmedabad": {"rain_base": 15, "flood_prob": 0.08, "traffic_base": 0.50},
}


def simulate_weather_feed() -> List[Dict]:
    """Simulate real-time weather disruption data for all cities."""
    rng = np.random.default_rng(int(datetime.utcnow().timestamp()) % 2**31)
    
    events = []
    for city, profile in CITY_WEATHER_PROFILES.items():
        # Add temporal noise to base values
        rainfall = max(0, profile["rain_base"] + rng.normal(0, 30))
        traffic = min(1.0, max(0.1, profile["traffic_base"] + rng.normal(0, 0.1)))
        
        # Rainfall → flood correlation
        flood_prob_adjusted = profile["flood_prob"] + (0.2 if rainfall > 100 else 0)
        is_flood = rng.random() < flood_prob_adjusted
        
        # Determine if this constitutes a disruption event
        severity = 0.0
        if rainfall > 80:
            severity += 0.3
        if is_flood:
            severity += 0.35
        if traffic > 0.85:
            severity += 0.15
        
        # Pollution inversely correlated with rain
        pollution = rng.random() < (0.5 if rainfall < 20 and traffic > 0.7 else 0.15)
        
        event = {
            "city": city,
            "timestamp": datetime.utcnow().isoformat(),
            "rainfall_mm": round(float(rainfall), 1),
            "flood_zone_active": bool(is_flood),
            "traffic_index": round(float(traffic), 3),
            "pollution_spike": bool(pollution),
            "disruption_severity": round(float(min(1.0, severity)), 3),
            "is_disruption": severity > 0.3,
        }
        events.append(event)
    
    return events


def simulate_worker_data(city_event: Dict, rng: np.random.Generator) -> Dict:
    """Simulate a worker's data in the context of a disruption event."""
    is_genuine = rng.random() > 0.08  # ~92% genuine
    
    if is_genuine:
        return {
            "city_risk_index": round(float(city_event["disruption_severity"]), 4),
            "rainfall_last_3day_avg": city_event["rainfall_mm"],
            "flood_zone_flag": int(city_event["flood_zone_active"]),
            "traffic_peak_index": city_event["traffic_index"],
            "pollution_spike_flag": int(city_event["pollution_spike"]),
            "parcel_demand_index": round(float(rng.uniform(0.3, 0.8)), 4),
            "historical_income_variance": round(float(rng.uniform(0.1, 0.5)), 4),
            "active_hours_ratio": round(float(rng.uniform(0.5, 0.95)), 4),
            "gps_jump_distance": round(float(rng.exponential(2.0)), 2),
            "claim_frequency_7day": round(float(rng.poisson(1.5)), 1),
            "nearby_claim_cluster_score": round(float(rng.uniform(0.05, 0.35)), 4),
            "is_genuine": True,
        }
    else:
        return {
            "city_risk_index": round(float(rng.uniform(0.1, 0.3)), 4),
            "rainfall_last_3day_avg": round(float(rng.uniform(5, 30)), 2),
            "flood_zone_flag": 0,
            "traffic_peak_index": round(float(rng.uniform(0.3, 0.5)), 4),
            "pollution_spike_flag": 0,
            "parcel_demand_index": round(float(rng.uniform(0.4, 0.9)), 4),
            "historical_income_variance": round(float(rng.uniform(0.3, 0.8)), 4),
            "active_hours_ratio": round(float(rng.uniform(0.05, 0.30)), 4),
            "gps_jump_distance": round(float(rng.uniform(15, 80)), 2),
            "claim_frequency_7day": round(float(rng.uniform(4, 10)), 1),
            "nearby_claim_cluster_score": round(float(rng.uniform(0.6, 0.95)), 4),
            "is_genuine": False,
        }


class ParametricScheduler:
    """Background scheduler for automated parametric claim processing."""
    
    def __init__(self):
        self.is_running = False
        self.cycle_count = 0
        self.decisions = []
        self.models = {}
        
    def load_models(self):
        """Load ML models for inference."""
        model_files = {
            "risk_model": MODELS_DIR / "risk_xgb.pkl",
            "income_loss_model": MODELS_DIR / "income_loss_model.pkl",
            "fraud_model": MODELS_DIR / "fraud_iforest.pkl",
            "fraud_scaler": MODELS_DIR / "fraud_scaler.pkl",
        }
        for name, path in model_files.items():
            if path.exists():
                self.models[name] = joblib.load(path)
                print(f"  ✅ Loaded {name}")
            else:
                print(f"  ⚠ Missing {name}")
    
    def engineer_features(self, data: dict) -> np.ndarray:
        """Compute derived features for model input."""
        rain_norm = data["rainfall_last_3day_avg"] / 350.0
        
        disruption_risk = min(1.0,
            rain_norm * 0.35 + data["flood_zone_flag"] * 0.25 +
            data["traffic_peak_index"] * 0.25 + data["pollution_spike_flag"] * 0.15)
        
        gps_stability = max(0, 1.0 - data["gps_jump_distance"] / 80.0)
        mobility_stability = min(1.0, gps_stability * 0.6 + data["active_hours_ratio"] * 0.4)
        
        demand_dev = abs(data["parcel_demand_index"] - 0.65)
        logistics_vol = min(1.0, demand_dev * 1.2 + data["historical_income_variance"] * 0.5)
        
        claim_norm = min(1.0, data["claim_frequency_7day"] / 10.0)
        behavioral_trust = min(1.0,
            data["active_hours_ratio"] * 0.35 + (1.0 - claim_norm) * 0.35 +
            (1.0 - data["nearby_claim_cluster_score"]) * 0.30)
        
        return np.array([[
            data["city_risk_index"], data["rainfall_last_3day_avg"],
            data["flood_zone_flag"], data["traffic_peak_index"],
            data["pollution_spike_flag"], data["parcel_demand_index"],
            data["historical_income_variance"], data["active_hours_ratio"],
            data["gps_jump_distance"], data["claim_frequency_7day"],
            data["nearby_claim_cluster_score"],
            disruption_risk, mobility_stability, logistics_vol, behavioral_trust,
            rain_norm * data["traffic_peak_index"],  # rain_traffic
            data["flood_zone_flag"] * claim_norm,     # flood_claim
            min(1.0, data["gps_jump_distance"] / 80.0) * claim_norm,  # gps_claim
        ]]), {
            "disruption_risk": disruption_risk,
            "mobility_stability": mobility_stability,
            "logistics_volatility": logistics_vol,
            "behavioral_trust": behavioral_trust,
        }
    
    def process_claim(self, worker_data: dict, city: str) -> dict:
        """Run the full AI pipeline on a single worker claim."""
        features, derived = self.engineer_features(worker_data)
        
        decision = {
            "timestamp": datetime.utcnow().isoformat(),
            "city": city,
            "input_data": worker_data,
            "derived_features": derived,
            "pipeline_results": {},
            "final_decision": None,
            "reasoning": [],
        }
        
        # Step 1: Risk prediction
        if "risk_model" in self.models:
            risk_prob = float(self.models["risk_model"].predict_proba(features)[0][1])
            risk_flag = bool(self.models["risk_model"].predict(features)[0])
            decision["pipeline_results"]["risk"] = {
                "probability": round(risk_prob, 4),
                "high_risk": risk_flag,
            }
            decision["reasoning"].append(
                f"Risk prediction: {'HIGH' if risk_flag else 'LOW'} (p={risk_prob:.3f})"
            )
        
        # Step 2: Income loss prediction
        if "income_loss_model" in self.models:
            loss_hours = float(self.models["income_loss_model"].predict(features)[0])
            loss_hours = max(0, round(loss_hours, 2))
            decision["pipeline_results"]["income_loss"] = {
                "expected_hours": loss_hours,
            }
            decision["reasoning"].append(
                f"Predicted income loss: {loss_hours:.1f} hours"
            )
        
        # Step 3: Fraud detection
        if "fraud_model" in self.models and "fraud_scaler" in self.models:
            fraud_features = np.array([[
                worker_data["gps_jump_distance"],
                worker_data["claim_frequency_7day"],
                worker_data["active_hours_ratio"],
                worker_data["nearby_claim_cluster_score"],
            ]])
            fraud_scaled = self.models["fraud_scaler"].transform(fraud_features)
            fraud_score_raw = self.models["fraud_model"].decision_function(fraud_scaled)[0]
            fraud_pred = self.models["fraud_model"].predict(fraud_scaled)[0]
            anomaly_score = float(max(0, min(1, 0.5 - fraud_score_raw)))
            
            decision["pipeline_results"]["fraud"] = {
                "anomaly_score": round(anomaly_score, 4),
                "is_suspicious": bool(fraud_pred == -1),
            }
            decision["reasoning"].append(
                f"Fraud score: {anomaly_score:.3f} ({'SUSPICIOUS' if fraud_pred == -1 else 'NORMAL'})"
            )
        else:
            anomaly_score = 0.0
        
        # Step 4: Trust score
        from ai_pipeline.trust_engine import compute_trust_score
        trust_result = compute_trust_score(
            mobility_stability_index=derived["mobility_stability"],
            behavioral_trust_index=derived["behavioral_trust"],
            fraud_anomaly_score=anomaly_score,
            disruption_risk_score=derived["disruption_risk"],
        )
        decision["pipeline_results"]["trust"] = {
            "score": trust_result["trust_score"],
            "recommendation": trust_result["recommendation"],
        }
        decision["reasoning"].append(
            f"Trust score: {trust_result['trust_score']:.3f} → {trust_result['recommendation']}"
        )
        
        # Final decision
        decision["final_decision"] = trust_result["recommendation"]
        decision["reasoning"].append(
            f"Final: {trust_result['explanation']}"
        )
        
        return decision
    
    async def run_cycle(self):
        """Execute one full disruption scan + claim processing cycle."""
        self.cycle_count += 1
        rng = np.random.default_rng(int(datetime.utcnow().timestamp()) % 2**31)
        
        print(f"\n{'='*60}")
        print(f"  🔄 Scheduler Cycle #{self.cycle_count} — {datetime.utcnow().isoformat()}")
        print(f"{'='*60}")
        
        # Step 1: Get weather feed
        weather_events = simulate_weather_feed()
        disruptions = [e for e in weather_events if e["is_disruption"]]
        print(f"\n  🌧 Weather feed: {len(weather_events)} cities, {len(disruptions)} disruptions")
        
        cycle_decisions = []
        
        for event in disruptions:
            print(f"\n  ⚡ Disruption in {event['city']} (severity: {event['disruption_severity']:.2f})")
            
            # Simulate 2-5 affected workers per disruption
            n_workers = rng.integers(2, 6)
            for w in range(n_workers):
                worker_data = simulate_worker_data(event, rng)
                decision = self.process_claim(worker_data, event["city"])
                cycle_decisions.append(decision)
                
                genuine_label = "✅ GENUINE" if worker_data["is_genuine"] else "🎭 FRAUD"
                print(f"    Worker {w+1}: {genuine_label} → {decision['final_decision']}")
        
        # Log decisions
        self.decisions.extend(cycle_decisions)
        self._save_log(cycle_decisions)
        
        stats = {
            "total_processed": len(cycle_decisions),
            "auto_approved": sum(1 for d in cycle_decisions if d["final_decision"] == "AUTO_APPROVE"),
            "manual_review": sum(1 for d in cycle_decisions if d["final_decision"] == "MANUAL_REVIEW"),
            "flagged": sum(1 for d in cycle_decisions if d["final_decision"] == "FLAG_SUSPICIOUS"),
            "auto_rejected": sum(1 for d in cycle_decisions if d["final_decision"] == "AUTO_REJECT"),
        }
        
        print(f"\n  📊 Cycle Summary:")
        print(f"    Processed: {stats['total_processed']}")
        print(f"    Auto-Approved: {stats['auto_approved']}")
        print(f"    Manual Review: {stats['manual_review']}")
        print(f"    Flagged: {stats['flagged']}")
        print(f"    Auto-Rejected: {stats['auto_rejected']}")
        
        return stats
    
    def _save_log(self, decisions: List[Dict]):
        """Save decision log to file."""
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOGS_DIR / f"decisions_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, "w") as f:
            json.dump(decisions, f, indent=2, default=str)
        print(f"\n  💾 Log saved to {log_file}")
    
    async def start(self, interval_seconds: int = 60, max_cycles: int = 3):
        """Start the scheduler loop."""
        print("\n🚀 Parametric Automation Scheduler Starting...")
        self.load_models()
        self.is_running = True
        
        cycle = 0
        while self.is_running and cycle < max_cycles:
            await self.run_cycle()
            cycle += 1
            if cycle < max_cycles:
                print(f"\n  ⏳ Next cycle in {interval_seconds}s...")
                await asyncio.sleep(interval_seconds)
        
        print(f"\n🏁 Scheduler completed {cycle} cycles")
    
    def stop(self):
        """Stop the scheduler."""
        self.is_running = False


# ─── Main Entry Point ──────────────────────────────────────

async def main():
    scheduler = ParametricScheduler()
    await scheduler.start(interval_seconds=5, max_cycles=3)


if __name__ == "__main__":
    asyncio.run(main())
