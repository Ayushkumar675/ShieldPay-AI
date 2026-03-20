"""
ShieldPay AI — Risk Prediction Model (XGBoost Classifier)
==========================================================
Binary classification: predicts high_income_loss_risk_flag

Training pipeline:
  1. Time-aware train/test split (80/20)
  2. 5-fold stratified cross-validation
  3. Metrics: accuracy, F1 (macro), ROC-AUC
  4. Feature importance bar chart
  5. SHAP explainability summary plot

Saved: models/saved/risk_xgb.pkl
"""

import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import json
from pathlib import Path
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import (
    accuracy_score, f1_score, roc_auc_score,
    classification_report, confusion_matrix, roc_curve
)
from xgboost import XGBClassifier

MODELS_DIR = Path(__file__).parent / "saved"
REPORTS_DIR = Path(__file__).parent.parent / "reports"
DATA_DIR = Path(__file__).parent.parent / "data"


def load_data():
    """Load engineered features dataset."""
    df = pd.read_csv(DATA_DIR / "engineered_features.csv")
    return df


def get_feature_columns():
    """Feature columns for risk model."""
    return [
        "city_risk_index", "rainfall_last_3day_avg", "flood_zone_flag",
        "traffic_peak_index", "pollution_spike_flag", "parcel_demand_index",
        "historical_income_variance", "active_hours_ratio", "gps_jump_distance",
        "claim_frequency_7day", "nearby_claim_cluster_score",
        "disruption_risk_score_feature", "mobility_stability_index",
        "logistics_volatility_feature", "behavioral_trust_index",
        "rain_traffic_interaction", "flood_claim_interaction", "gps_claim_anomaly",
    ]


def time_aware_split(df, test_ratio=0.2):
    """
    Simulate time-aware split: treat row order as temporal ordering.
    Last 20% of data = test set (future data).
    """
    split_idx = int(len(df) * (1 - test_ratio))
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()
    print(f"  Train: {len(train_df)} rows | Test: {len(test_df)} rows")
    return train_df, test_df


def train_risk_model():
    """Full training pipeline for risk classification."""
    print("=" * 60)
    print("  ShieldPay AI — Risk Prediction Model Training")
    print("=" * 60)
    
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    df = load_data()
    features = get_feature_columns()
    target = "high_income_loss_risk_flag"
    
    # ── 1. Time-aware split ─────────────────────────────────
    print("\n📊 Step 1: Time-Aware Train/Test Split")
    train_df, test_df = time_aware_split(df)
    
    X_train = train_df[features].values
    y_train = train_df[target].values
    X_test = test_df[features].values
    y_test = test_df[target].values
    
    # ── 2. Model definition ─────────────────────────────────
    print("\n🔧 Step 2: XGBoost Classifier")
    model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=0.5,
        reg_lambda=1.0,
        scale_pos_weight=len(y_train[y_train == 0]) / max(len(y_train[y_train == 1]), 1),
        random_state=42,
        eval_metric="logloss",
        use_label_encoder=False,
    )
    
    # ── 3. Cross-validation ─────────────────────────────────
    print("\n📈 Step 3: 5-Fold Stratified Cross-Validation")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_results = cross_validate(
        model, X_train, y_train, cv=cv,
        scoring=["accuracy", "f1_macro", "roc_auc"],
        return_train_score=True,
    )
    
    cv_metrics = {
        "cv_accuracy_mean": float(np.mean(cv_results["test_accuracy"])),
        "cv_accuracy_std": float(np.std(cv_results["test_accuracy"])),
        "cv_f1_macro_mean": float(np.mean(cv_results["test_f1_macro"])),
        "cv_f1_macro_std": float(np.std(cv_results["test_f1_macro"])),
        "cv_roc_auc_mean": float(np.mean(cv_results["test_roc_auc"])),
        "cv_roc_auc_std": float(np.std(cv_results["test_roc_auc"])),
    }
    
    print(f"  Accuracy: {cv_metrics['cv_accuracy_mean']:.4f} ± {cv_metrics['cv_accuracy_std']:.4f}")
    print(f"  F1 Macro: {cv_metrics['cv_f1_macro_mean']:.4f} ± {cv_metrics['cv_f1_macro_std']:.4f}")
    print(f"  ROC-AUC:  {cv_metrics['cv_roc_auc_mean']:.4f} ± {cv_metrics['cv_roc_auc_std']:.4f}")
    
    # ── 4. Final model fit ──────────────────────────────────
    print("\n🎯 Step 4: Final Model Training on Full Train Set")
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )
    
    # ── 5. Test set evaluation ──────────────────────────────
    print("\n📋 Step 5: Test Set Evaluation")
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    test_metrics = {
        "test_accuracy": float(accuracy_score(y_test, y_pred)),
        "test_f1_macro": float(f1_score(y_test, y_pred, average="macro")),
        "test_roc_auc": float(roc_auc_score(y_test, y_pred_proba)),
    }
    
    print(f"  Accuracy: {test_metrics['test_accuracy']:.4f}")
    print(f"  F1 Macro: {test_metrics['test_f1_macro']:.4f}")
    print(f"  ROC-AUC:  {test_metrics['test_roc_auc']:.4f}")
    print(f"\n  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["Low Risk", "High Risk"]))
    
    # ── 6. Feature importance plot ──────────────────────────
    print("📊 Step 6: Feature Importance Plot")
    importances = model.feature_importances_
    sorted_idx = np.argsort(importances)
    
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(range(len(sorted_idx)), importances[sorted_idx], color="#4FC3F7")
    ax.set_yticks(range(len(sorted_idx)))
    ax.set_yticklabels([features[i] for i in sorted_idx], fontsize=9)
    ax.set_xlabel("Feature Importance (Gain)", fontsize=11)
    ax.set_title("Risk Model — XGBoost Feature Importance", fontsize=14, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    importance_path = REPORTS_DIR / "risk_feature_importance.png"
    fig.savefig(importance_path, dpi=150)
    plt.close()
    print(f"  💾 Saved to {importance_path}")
    
    # ── 7. ROC Curve ────────────────────────────────────────
    fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(fpr, tpr, color="#E91E63", linewidth=2,
            label=f"ROC AUC = {test_metrics['test_roc_auc']:.3f}")
    ax.plot([0, 1], [0, 1], "k--", alpha=0.3)
    ax.set_xlabel("False Positive Rate", fontsize=12)
    ax.set_ylabel("True Positive Rate", fontsize=12)
    ax.set_title("Risk Model — ROC Curve", fontsize=14, fontweight="bold")
    ax.legend(fontsize=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    roc_path = REPORTS_DIR / "risk_roc_curve.png"
    fig.savefig(roc_path, dpi=150)
    plt.close()
    print(f"  💾 Saved to {roc_path}")
    
    # ── 8. SHAP Explainability ──────────────────────────────
    print("\n🔍 Step 7: SHAP Explainability")
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        # Use a sample for speed
        sample_size = min(500, len(X_test))
        X_sample = X_test[:sample_size]
        shap_values = explainer.shap_values(X_sample)
        
        fig, ax = plt.subplots(figsize=(10, 8))
        shap.summary_plot(
            shap_values, X_sample,
            feature_names=features,
            show=False,
            plot_size=(10, 8),
        )
        shap_path = REPORTS_DIR / "risk_shap_summary.png"
        plt.tight_layout()
        plt.savefig(shap_path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  💾 Saved SHAP summary to {shap_path}")
    except ImportError:
        print("  ⚠ SHAP not installed, skipping explainability plot")
    except Exception as e:
        print(f"  ⚠ SHAP computation error: {e}")
    
    # ── 9. Save model ───────────────────────────────────────
    model_path = MODELS_DIR / "risk_xgb.pkl"
    joblib.dump(model, model_path)
    print(f"\n💾 Model saved to {model_path}")
    
    # Save all metrics
    all_metrics = {**cv_metrics, **test_metrics, "features": features}
    metrics_path = REPORTS_DIR / "risk_model_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(all_metrics, f, indent=2)
    print(f"💾 Metrics saved to {metrics_path}")
    
    return model, all_metrics


if __name__ == "__main__":
    train_risk_model()
