"""
ShieldPay AI — Synthetic Logistics Dataset Generator
Generates realistic mock data for workers, delivery history,
disruption events, and fraud patterns for development & demo.
"""
import json
import random
import os
from datetime import datetime, timedelta
from typing import List, Dict
import uuid

# ─── Configuration ────────────────────────────────────────

NUM_WORKERS = 200
NUM_WAREHOUSES = 15
NUM_DAYS_HISTORY = 90
NUM_DISRUPTION_EVENTS = 60
NUM_FRAUD_WORKERS = 12  # ~6% fraud rate

CITIES = [
    {"name": "Mumbai", "lat": 19.076, "lng": 72.8777},
    {"name": "Delhi", "lat": 28.7041, "lng": 77.1025},
    {"name": "Bangalore", "lat": 12.9716, "lng": 77.5946},
    {"name": "Hyderabad", "lat": 17.385, "lng": 78.4867},
    {"name": "Chennai", "lat": 13.0827, "lng": 80.2707},
    {"name": "Pune", "lat": 18.5204, "lng": 73.8567},
    {"name": "Kolkata", "lat": 22.5726, "lng": 88.3639},
    {"name": "Ahmedabad", "lat": 23.0225, "lng": 72.5714},
]

PLATFORMS = ["amazon", "flipkart", "meesho", "jiomart"]

DISRUPTION_TYPES = [
    "weather", "warehouse_shutdown", "curfew_lockdown",
    "traffic_gridlock", "parcel_allocation_drop"
]

WEATHER_CONDITIONS = [
    "heavy_rain", "cyclone_warning", "extreme_heat",
    "flooding", "hailstorm", "dense_fog"
]

WAREHOUSE_ISSUES = [
    "power_failure", "flooding", "equipment_breakdown",
    "labor_strike", "fire_incident", "capacity_overflow"
]


def gen_id():
    return str(uuid.uuid4())


def random_phone():
    return f"+91{random.randint(7000000000, 9999999999)}"


def jitter(base_lat, base_lng, km_range=10):
    """Add random GPS jitter within km_range."""
    delta = km_range / 111.0  # ~1 degree ≈ 111km
    return (
        round(base_lat + random.uniform(-delta, delta), 6),
        round(base_lng + random.uniform(-delta, delta), 6)
    )


# ─── Warehouse Generator ─────────────────────────────────

def generate_warehouses() -> List[Dict]:
    warehouses = []
    for i in range(NUM_WAREHOUSES):
        city = random.choice(CITIES)
        lat, lng = jitter(city["lat"], city["lng"], 15)
        warehouses.append({
            "id": f"WH-{i+1:03d}",
            "name": f"{city['name']} Hub {i+1}",
            "city": city["name"],
            "lat": lat,
            "lng": lng,
            "zone": f"ZONE-{city['name'][:3].upper()}-{random.randint(1,5)}",
            "avg_daily_dispatch": random.randint(500, 5000),
            "risk_level": round(random.uniform(0.1, 0.8), 2),
        })
    return warehouses


# ─── Worker Generator ────────────────────────────────────

def generate_workers(warehouses: List[Dict]) -> List[Dict]:
    workers = []
    fraud_indices = set(random.sample(range(NUM_WORKERS), NUM_FRAUD_WORKERS))

    for i in range(NUM_WORKERS):
        wh = random.choice(warehouses)
        lat, lng = jitter(wh["lat"], wh["lng"], 5)
        is_fraud = i in fraud_indices
        avg_parcels = random.randint(15, 60)

        workers.append({
            "id": gen_id(),
            "name": f"Worker_{i+1:04d}",
            "email": f"worker{i+1}@shieldpay.dev",
            "phone": random_phone(),
            "platform": random.choice(PLATFORMS),
            "warehouse_id": wh["id"],
            "city": wh["city"],
            "home_location": {"lat": lat, "lng": lng},
            "avg_daily_parcels": avg_parcels,
            "avg_daily_income": round(avg_parcels * random.uniform(12, 22), 2),
            "reliability_score": round(random.uniform(0.3, 0.6) if is_fraud else random.uniform(0.7, 1.0), 3),
            "is_fraud_actor": is_fraud,
            "device_signals": {
                "is_emulator": is_fraud and random.random() < 0.4,
                "is_rooted": is_fraud and random.random() < 0.3,
                "app_install_age_days": random.randint(1, 30) if is_fraud else random.randint(60, 500),
                "background_location_streaming": is_fraud and random.random() < 0.5,
                "accelerometer_available": not (is_fraud and random.random() < 0.2),
            },
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(30, 365))).isoformat(),
        })
    return workers


# ─── Delivery History Generator ──────────────────────────

def generate_delivery_history(workers: List[Dict]) -> List[Dict]:
    history = []
    for worker in workers:
        base_parcels = worker["avg_daily_parcels"]
        for day_offset in range(NUM_DAYS_HISTORY):
            date = (datetime.utcnow() - timedelta(days=day_offset)).strftime("%Y-%m-%d")
            # Add realistic variance: weekends lower, festivals spike
            day_of_week = (datetime.utcnow() - timedelta(days=day_offset)).weekday()
            weekend_factor = 0.6 if day_of_week >= 5 else 1.0
            seasonal_noise = random.uniform(0.7, 1.3)
            assigned = max(0, int(base_parcels * weekend_factor * seasonal_noise))
            # Fraud actors may show suspicious patterns
            if worker.get("is_fraud_actor") and random.random() < 0.15:
                delivered = random.randint(0, max(1, assigned // 4))  # suspiciously low
            else:
                delivered = max(0, assigned - random.randint(0, max(1, assigned // 8)))

            history.append({
                "worker_id": worker["id"],
                "date": date,
                "parcels_assigned": assigned,
                "parcels_delivered": delivered,
                "income_earned": round(delivered * random.uniform(12, 22), 2),
                "hours_active": round(random.uniform(4, 12) if assigned > 0 else 0, 1),
                "gps_distance_km": round(random.uniform(20, 80) if delivered > 5 else random.uniform(0, 5), 1),
            })
    return history


# ─── Disruption Events Generator ─────────────────────────

def generate_disruptions(warehouses: List[Dict]) -> List[Dict]:
    disruptions = []
    for i in range(NUM_DISRUPTION_EVENTS):
        dtype = random.choice(DISRUPTION_TYPES)
        wh = random.choice(warehouses)
        day_offset = random.randint(0, NUM_DAYS_HISTORY)
        detected = datetime.utcnow() - timedelta(days=day_offset, hours=random.randint(0, 23))
        duration_hours = random.randint(2, 72)

        event = {
            "id": gen_id(),
            "type": dtype,
            "severity": round(random.uniform(0.3, 1.0), 2),
            "affected_zone": wh["zone"],
            "affected_warehouse_ids": [wh["id"]],
            "location": {"lat": wh["lat"], "lng": wh["lng"], "city": wh["city"]},
            "detected_at": detected.isoformat(),
            "resolved_at": (detected + timedelta(hours=duration_hours)).isoformat(),
            "is_active": day_offset < 2,
        }

        if dtype == "weather":
            event["weather_data"] = {
                "condition": random.choice(WEATHER_CONDITIONS),
                "rainfall_mm": round(random.uniform(20, 200), 1),
                "wind_speed_kmh": round(random.uniform(15, 120), 1),
                "temperature_c": round(random.uniform(10, 48), 1),
            }
            event["description"] = f"{event['weather_data']['condition'].replace('_', ' ').title()} in {wh['city']}"
        elif dtype == "warehouse_shutdown":
            issue = random.choice(WAREHOUSE_ISSUES)
            event["description"] = f"{wh['name']} shutdown: {issue.replace('_', ' ')}"
        elif dtype == "curfew_lockdown":
            event["description"] = f"Regional curfew in {wh['zone']}"
        elif dtype == "traffic_gridlock":
            event["traffic_data"] = {
                "congestion_index": round(random.uniform(0.7, 1.0), 2),
                "avg_speed_kmh": round(random.uniform(3, 15), 1),
            }
            event["description"] = f"Severe traffic gridlock near {wh['name']}"
        else:
            event["description"] = f"Parcel allocation drop at {wh['name']}"

        disruptions.append(event)
    return disruptions


# ─── Fraud Patterns Generator ────────────────────────────

def generate_fraud_patterns(workers: List[Dict]) -> Dict:
    fraud_workers = [w for w in workers if w.get("is_fraud_actor")]
    patterns = {
        "gps_spoofing_events": [],
        "coordinated_claim_spikes": [],
        "fraud_rings": [],
    }

    # GPS spoofing events
    for fw in fraud_workers:
        for _ in range(random.randint(2, 8)):
            patterns["gps_spoofing_events"].append({
                "worker_id": fw["id"],
                "original_location": fw["home_location"],
                "spoofed_location": {
                    "lat": fw["home_location"]["lat"] + random.uniform(0.5, 2.0),
                    "lng": fw["home_location"]["lng"] + random.uniform(0.5, 2.0),
                },
                "teleport_distance_km": round(random.uniform(50, 300), 1),
                "timestamp": (datetime.utcnow() - timedelta(days=random.randint(0, 30))).isoformat(),
            })

    # Coordinated claim spikes (groups of 3-5 fraud workers claiming simultaneously)
    for _ in range(5):
        ring = random.sample(fraud_workers, min(random.randint(3, 5), len(fraud_workers)))
        spike_time = datetime.utcnow() - timedelta(days=random.randint(1, 20))
        patterns["coordinated_claim_spikes"].append({
            "worker_ids": [w["id"] for w in ring],
            "timestamp": spike_time.isoformat(),
            "claim_window_minutes": random.randint(5, 30),
            "total_amount_claimed": round(sum(random.uniform(500, 2000) for _ in ring), 2),
        })

    # Fraud rings
    if len(fraud_workers) >= 3:
        ring_size = min(random.randint(3, 6), len(fraud_workers))
        ring_members = random.sample(fraud_workers, ring_size)
        patterns["fraud_rings"].append({
            "id": gen_id(),
            "worker_ids": [w["id"] for w in ring_members],
            "detected_pattern": "temporal_claim_clustering + device_similarity",
            "confidence": round(random.uniform(0.7, 0.95), 2),
            "total_suspicious_claims": random.randint(8, 25),
        })

    return patterns


# ─── Main Generator ──────────────────────────────────────

def generate_all():
    print("🏗  Generating synthetic logistics dataset...")

    warehouses = generate_warehouses()
    print(f"  ✅ {len(warehouses)} warehouses")

    workers = generate_workers(warehouses)
    print(f"  ✅ {len(workers)} workers ({NUM_FRAUD_WORKERS} fraud actors)")

    delivery_history = generate_delivery_history(workers)
    print(f"  ✅ {len(delivery_history)} delivery history records")

    disruptions = generate_disruptions(warehouses)
    print(f"  ✅ {len(disruptions)} disruption events")

    fraud_patterns = generate_fraud_patterns(workers)
    print(f"  ✅ Fraud patterns: {len(fraud_patterns['gps_spoofing_events'])} spoof events, "
          f"{len(fraud_patterns['coordinated_claim_spikes'])} claim spikes, "
          f"{len(fraud_patterns['fraud_rings'])} rings")

    # Save datasets
    output_dir = os.path.join(os.path.dirname(__file__), "datasets")
    os.makedirs(output_dir, exist_ok=True)

    datasets = {
        "warehouses.json": warehouses,
        "workers.json": workers,
        "delivery_history.json": delivery_history,
        "disruptions.json": disruptions,
        "fraud_patterns.json": fraud_patterns,
    }

    for filename, data in datasets.items():
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"  💾 Saved {filepath}")

    print(f"\n🎉 Dataset generation complete! Output: {output_dir}")
    return datasets


if __name__ == "__main__":
    generate_all()
