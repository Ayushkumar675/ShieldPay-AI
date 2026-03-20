"""
ShieldPay AI — Master Pipeline Runner
=======================================
Runs the full ML pipeline sequentially:

1. Generate synthetic dataset (8500 rows)
2. Engineer features (18 columns)
3. Train Risk Prediction Model (XGBoost Classifier)
4. Train Income Loss Regression Model (XGBoost Regressor)
5. Train Fraud Detection Model (IsolationForest)
6. Generate Evaluation Report
"""

import time
from pathlib import Path


def run_full_pipeline():
    """Execute the complete ML pipeline."""
    start = time.time()
    
    print("\n" + "🔷" * 30)
    print("  ShieldPay AI — Full ML Pipeline")
    print("🔷" * 30)
    
    # ── Step 1: Generate Dataset ────────────────────────────
    print("\n\n" + "=" * 60)
    print("  STEP 1 / 6 — Synthetic Dataset Generation")
    print("=" * 60)
    from ai_pipeline.data_generator import generate_dataset, save_dataset, print_summary
    df = generate_dataset()
    save_dataset(df)
    print_summary(df)
    
    # ── Step 2: Feature Engineering ─────────────────────────
    print("\n\n" + "=" * 60)
    print("  STEP 2 / 6 — Feature Engineering")
    print("=" * 60)
    from ai_pipeline.feature_engineering import run_pipeline as feature_pipeline
    feature_pipeline()
    
    # ── Step 3: Train Risk Model ────────────────────────────
    print("\n\n" + "=" * 60)
    print("  STEP 3 / 6 — Risk Prediction Model")
    print("=" * 60)
    from ai_pipeline.models.risk_model import train_risk_model
    train_risk_model()
    
    # ── Step 4: Train Income Loss Model ─────────────────────
    print("\n\n" + "=" * 60)
    print("  STEP 4 / 6 — Income Loss Regression Model")
    print("=" * 60)
    from ai_pipeline.models.income_loss_model import train_income_loss_model
    train_income_loss_model()
    
    # ── Step 5: Train Fraud Detection Model ─────────────────
    print("\n\n" + "=" * 60)
    print("  STEP 5 / 6 — Fraud Detection Model")
    print("=" * 60)
    from ai_pipeline.models.fraud_model import train_fraud_model
    train_fraud_model()
    
    # ── Step 6: Generate Evaluation Report ──────────────────
    print("\n\n" + "=" * 60)
    print("  STEP 6 / 6 — Evaluation Report")
    print("=" * 60)
    from ai_pipeline.evaluation_report import generate_report
    generate_report()
    
    # ── Summary ─────────────────────────────────────────────
    elapsed = time.time() - start
    
    print("\n\n" + "🔷" * 30)
    print("  ✅ PIPELINE COMPLETE")
    print("🔷" * 30)
    print(f"\n  ⏱ Total time: {elapsed:.1f}s")
    
    # List all outputs
    base = Path(__file__).parent
    print(f"\n  📁 Output files:")
    
    data_dir = base / "data"
    if data_dir.exists():
        for f in sorted(data_dir.iterdir()):
            if f.is_file():
                size_kb = f.stat().st_size / 1024
                print(f"    📊 data/{f.name} ({size_kb:.1f} KB)")
    
    models_dir = base / "models" / "saved"
    if models_dir.exists():
        for f in sorted(models_dir.iterdir()):
            if f.is_file():
                size_kb = f.stat().st_size / 1024
                print(f"    🧠 models/saved/{f.name} ({size_kb:.1f} KB)")
    
    reports_dir = base / "reports"
    if reports_dir.exists():
        for f in sorted(reports_dir.iterdir()):
            if f.is_file():
                size_kb = f.stat().st_size / 1024
                print(f"    📋 reports/{f.name} ({size_kb:.1f} KB)")
    
    print(f"\n  🚀 API Server: python -m ai_pipeline.api_server")
    print(f"  🔄 Scheduler:  python -m ai_pipeline.scheduler")


if __name__ == "__main__":
    run_full_pipeline()
