"""
ShieldPay AI — Evaluation Report Generator
=============================================
Auto-generates comprehensive evaluation report covering:

  • Model performance metrics (accuracy, F1, ROC, MAE, RMSE, R²)
  • Feature importance rankings
  • Fraud detection threshold analysis
  • AI decision explanation templates

Output: reports/evaluation_report.md
"""

import json
import os
from datetime import datetime
from pathlib import Path

REPORTS_DIR = Path(__file__).parent / "reports"


def load_metrics(filename: str) -> dict:
    """Load metrics JSON file."""
    path = REPORTS_DIR / filename
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def generate_risk_model_section(metrics: dict) -> str:
    """Generate the risk model performance section."""
    if not metrics:
        return "### Risk Model\n⚠ No metrics available. Run training pipeline first.\n"
    
    return f"""### Risk Prediction Model (XGBoost Classifier)

**Target:** `high_income_loss_risk_flag` (binary)

#### Cross-Validation Results (5-Fold Stratified)

| Metric | Mean | Std |
|--------|------|-----|
| Accuracy | {metrics.get('cv_accuracy_mean', 0):.4f} | ±{metrics.get('cv_accuracy_std', 0):.4f} |
| F1 Macro | {metrics.get('cv_f1_macro_mean', 0):.4f} | ±{metrics.get('cv_f1_macro_std', 0):.4f} |
| ROC-AUC | {metrics.get('cv_roc_auc_mean', 0):.4f} | ±{metrics.get('cv_roc_auc_std', 0):.4f} |

#### Test Set Results

| Metric | Score |
|--------|-------|
| Accuracy | {metrics.get('test_accuracy', 0):.4f} |
| F1 Macro | {metrics.get('test_f1_macro', 0):.4f} |
| ROC-AUC | {metrics.get('test_roc_auc', 0):.4f} |

> [!NOTE]
> Time-aware train/test split used (80/20). Test set represents future temporal data.

![Feature Importance](risk_feature_importance.png)
![ROC Curve](risk_roc_curve.png)
![SHAP Summary](risk_shap_summary.png)
"""


def generate_income_loss_section(metrics: dict) -> str:
    """Generate the income loss model section."""
    if not metrics:
        return "### Income Loss Model\n⚠ No metrics available.\n"
    
    return f"""### Income Loss Regression Model (XGBoost Regressor)

**Target:** `expected_income_loss_hours_next_week` (continuous)

#### Rolling Window Cross-Validation (5-Fold Expanding)

| Metric | Mean | Std |
|--------|------|-----|
| MAE | {metrics.get('cv_mae_mean', 0):.3f} | ±{metrics.get('cv_mae_std', 0):.3f} |
| RMSE | {metrics.get('cv_rmse_mean', 0):.3f} | ±{metrics.get('cv_rmse_std', 0):.3f} |
| R² | {metrics.get('cv_r2_mean', 0):.4f} | ±{metrics.get('cv_r2_std', 0):.4f} |

#### Test Set Results

| Metric | Score |
|--------|-------|
| MAE | {metrics.get('test_mae', 0):.3f} |
| RMSE | {metrics.get('test_rmse', 0):.3f} |
| R² | {metrics.get('test_r2', 0):.4f} |

![Regression Diagnostics](income_loss_diagnostics.png)
![Feature Importance](income_loss_feature_importance.png)
"""


def generate_fraud_section(metrics: dict) -> str:
    """Generate the fraud detection section."""
    if not metrics:
        return "### Fraud Detection Model\n⚠ No metrics available.\n"
    
    # Threshold analysis table
    threshold_rows = ""
    for t in metrics.get("threshold_analysis", []):
        threshold_rows += f"| P{t['percentile']} | {t['threshold']:.4f} | {t['flagged_count']} | {t['flagged_pct']}% |\n"
    
    # Feature analysis table
    feature_rows = ""
    for feat, vals in metrics.get("feature_analysis", {}).items():
        feature_rows += f"| `{feat}` | {vals['normal_mean']:.3f} | {vals['fraud_mean']:.3f} | {vals['fraud_to_normal_ratio']:.2f}x |\n"
    
    return f"""### Fraud Detection Model (IsolationForest)

**Approach:** Unsupervised anomaly detection
**Contamination:** {metrics.get('contamination', 'N/A')}
**Optimal Threshold:** P{metrics.get('threshold_percentile', 92)} = {metrics.get('optimal_threshold', 0):.4f}

#### Threshold Sensitivity Analysis

| Percentile | Threshold | Flagged Count | Flagged % |
|------------|-----------|---------------|-----------|
{threshold_rows}
> [!IMPORTANT]
> P92 was selected to align with the ~8% expected fraud rate in the synthetic data. In production, this should be calibrated with labeled fraud data.

#### Feature Contribution (Normal vs Flagged Workers)

| Feature | Normal Mean | Flagged Mean | Ratio |
|---------|-------------|--------------|-------|
{feature_rows}
![Fraud Analysis](fraud_detection_analysis.png)
"""


def generate_decision_explanation_section() -> str:
    """Generate AI decision explanation templates."""
    return """### AI Decision Explanation Logic

The trust score fusion engine produces 4 possible recommendations:

| Trust Score | Recommendation | Action |
|-------------|----------------|--------|
| ≥ 0.75 | `AUTO_APPROVE` | Claim automatically approved and queued for payout |
| 0.50 – 0.74 | `MANUAL_REVIEW` | Claim sent to human reviewer with AI analysis |
| 0.30 – 0.49 | `FLAG_SUSPICIOUS` | Claim flagged for fraud investigation |
| < 0.30 | `AUTO_REJECT` | Claim automatically rejected |

#### Trust Score Components

```
trust_score = (
    mobility_stability_index    × 0.25  +   # GPS consistency + activity
    behavioral_trust_index      × 0.25  +   # Claims pattern + engagement
    (1 - fraud_anomaly_score)   × 0.30  +   # Fraud inverse (most weighted)
    disruption_risk_match       × 0.20      # Environmental disruption
)
```

#### Decision Flow

```
Weather Feed → Risk Model (XGBoost) → Disruption probability
                    ↓
Worker Features → Fraud Model (IsolationForest) → Anomaly score
                    ↓
All Signals → Trust Score Fusion → Recommendation
                    ↓
              AUTO_APPROVE / MANUAL_REVIEW / FLAG / AUTO_REJECT
                    ↓
              Decision logged with full reasoning chain
```

> [!TIP]
> The fraud safety signal carries 30% weight — the heaviest component — because
> preventing fraudulent payouts has the highest financial impact.
"""


def generate_report():
    """Generate the complete evaluation report."""
    print("=" * 60)
    print("  ShieldPay AI — Generating Evaluation Report")
    print("=" * 60)
    
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    risk_metrics = load_metrics("risk_model_metrics.json")
    income_metrics = load_metrics("income_loss_metrics.json")
    fraud_metrics = load_metrics("fraud_model_metrics.json")
    
    report = f"""# ShieldPay AI — Model Evaluation Report

**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
**Pipeline Version:** 1.0.0

---

## Executive Summary

This report evaluates the ML intelligence layer of the ShieldPay AI parametric insurance platform.
Three AI models work together to assess delivery worker claims:

1. **Risk Classifier** — Predicts whether a worker faces high income loss risk
2. **Income Loss Regressor** — Estimates expected income loss hours
3. **Fraud Detector** — Identifies anomalous claim patterns

These models feed into a **Trust Score Fusion Engine** that determines the final
claim decision (auto-approve, manual review, flag, or auto-reject).

---

## Model Performance

{generate_risk_model_section(risk_metrics)}

---

{generate_income_loss_section(income_metrics)}

---

{generate_fraud_section(fraud_metrics)}

---

{generate_decision_explanation_section()}

---

## Feature Engineering Summary

| Derived Feature | Description | Components |
|-----------------|-------------|------------|
| `disruption_risk_score_feature` | Environmental disruption signal | rainfall + flood + traffic + pollution |
| `mobility_stability_index` | Worker mobility consistency | GPS stability + active hours |
| `logistics_volatility_feature` | Demand/income volatility | Demand variance + income variance |
| `behavioral_trust_index` | Worker trustworthiness signal | Activity + claim pattern + clustering |
| `rain_traffic_interaction` | Compounding disruption | rainfall × traffic |
| `flood_claim_interaction` | Genuine disruption claims | flood × claims |
| `gps_claim_anomaly` | Fraud signal | GPS jump × claim rate |

---

## Recommendations for Production

> [!WARNING]
> The current models are trained on **synthetic data**. Before production deployment:

1. **Data Integration** — Replace synthetic data with real weather APIs, delivery platform data, and historical claims
2. **Label Quality** — Obtain verified fraud labels from investigations team
3. **Model Retraining** — Implement automated retraining on new data quarterly
4. **Threshold Calibration** — Tune fraud threshold using business cost matrix
5. **A/B Testing** — Run shadow mode alongside manual review before full automation
6. **Monitoring** — Track feature drift, model performance degradation, and decision outcome feedback
"""
    
    report_path = REPORTS_DIR / "evaluation_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n💾 Report saved to {report_path}")
    print(f"   Size: {len(report)} characters")
    return report_path


if __name__ == "__main__":
    generate_report()
