"""
ShieldPay AI — Income Loss Regression Model (XGBoost Regressor)
================================================================
Predicts: expected_income_loss_hours_next_week (continuous)

Training pipeline:
  1. Rolling window validation (expanding window, 5 folds)
  2. Metrics: MAE, RMSE, R²
  3. Feature importance analysis

Saved: models/saved/income_loss_model.pkl
"""

import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import json
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

MODELS_DIR = Path(__file__).parent / "saved"
REPORTS_DIR = Path(__file__).parent.parent / "reports"
DATA_DIR = Path(__file__).parent.parent / "data"


def get_feature_columns():
    """Feature columns for income loss model."""
    return [
        "city_risk_index", "rainfall_last_3day_avg", "flood_zone_flag",
        "traffic_peak_index", "pollution_spike_flag", "parcel_demand_index",
        "historical_income_variance", "active_hours_ratio", "gps_jump_distance",
        "claim_frequency_7day", "nearby_claim_cluster_score",
        "disruption_risk_score_feature", "mobility_stability_index",
        "logistics_volatility_feature", "behavioral_trust_index",
        "rain_traffic_interaction", "flood_claim_interaction", "gps_claim_anomaly",
    ]


def rolling_window_cv(X, y, n_splits=5):
    """
    Expanding window cross-validation (time-series style).
    Each fold uses all data up to a cutoff for training,
    and the next chunk for validation.
    """
    n = len(X)
    fold_size = n // (n_splits + 1)
    
    folds = []
    for i in range(n_splits):
        train_end = fold_size * (i + 2)
        val_start = train_end
        val_end = min(val_start + fold_size, n)
        
        if val_end <= val_start:
            break
            
        train_idx = np.arange(0, train_end)
        val_idx = np.arange(val_start, val_end)
        folds.append((train_idx, val_idx))
        
    return folds


def train_income_loss_model():
    """Full training pipeline for income loss regression."""
    print("=" * 60)
    print("  ShieldPay AI — Income Loss Regression Model Training")
    print("=" * 60)
    
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load data
    df = pd.read_csv(DATA_DIR / "engineered_features.csv")
    features = get_feature_columns()
    target = "expected_income_loss_hours_next_week"
    
    X = df[features].values
    y = df[target].values
    
    # ── 1. Model definition ─────────────────────────────────
    print("\n🔧 Step 1: XGBoost Regressor")
    model = XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=5,
        gamma=0.1,
        reg_alpha=0.5,
        reg_lambda=1.0,
        random_state=42,
    )
    
    # ── 2. Rolling window cross-validation ──────────────────
    print("\n📈 Step 2: Rolling Window Cross-Validation (5 folds)")
    folds = rolling_window_cv(X, y, n_splits=5)
    
    cv_mae, cv_rmse, cv_r2 = [], [], []
    
    for i, (train_idx, val_idx) in enumerate(folds):
        X_tr, y_tr = X[train_idx], y[train_idx]
        X_val, y_val = X[val_idx], y[val_idx]
        
        fold_model = XGBRegressor(**model.get_params())
        fold_model.fit(X_tr, y_tr, verbose=False)
        
        y_pred = fold_model.predict(X_val)
        
        mae = mean_absolute_error(y_val, y_pred)
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        r2 = r2_score(y_val, y_pred)
        
        cv_mae.append(mae)
        cv_rmse.append(rmse)
        cv_r2.append(r2)
        
        print(f"  Fold {i+1}: MAE={mae:.3f}, RMSE={rmse:.3f}, R²={r2:.4f} "
              f"(train={len(train_idx)}, val={len(val_idx)})")
    
    cv_metrics = {
        "cv_mae_mean": float(np.mean(cv_mae)),
        "cv_mae_std": float(np.std(cv_mae)),
        "cv_rmse_mean": float(np.mean(cv_rmse)),
        "cv_rmse_std": float(np.std(cv_rmse)),
        "cv_r2_mean": float(np.mean(cv_r2)),
        "cv_r2_std": float(np.std(cv_r2)),
    }
    
    print(f"\n  Mean MAE:  {cv_metrics['cv_mae_mean']:.3f} ± {cv_metrics['cv_mae_std']:.3f}")
    print(f"  Mean RMSE: {cv_metrics['cv_rmse_mean']:.3f} ± {cv_metrics['cv_rmse_std']:.3f}")
    print(f"  Mean R²:   {cv_metrics['cv_r2_mean']:.4f} ± {cv_metrics['cv_r2_std']:.4f}")
    
    # ── 3. Final model on 80/20 split ───────────────────────
    print("\n🎯 Step 3: Final Model Training")
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )
    
    y_pred = model.predict(X_test)
    test_metrics = {
        "test_mae": float(mean_absolute_error(y_test, y_pred)),
        "test_rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
        "test_r2": float(r2_score(y_test, y_pred)),
    }
    
    print(f"  Test MAE:  {test_metrics['test_mae']:.3f}")
    print(f"  Test RMSE: {test_metrics['test_rmse']:.3f}")
    print(f"  Test R²:   {test_metrics['test_r2']:.4f}")
    
    # ── 4. Actual vs Predicted Plot ─────────────────────────
    print("\n📊 Step 4: Actual vs Predicted Plot")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Scatter plot
    ax1.scatter(y_test, y_pred, alpha=0.3, s=10, color="#7C4DFF")
    ax1.plot([0, y_test.max()], [0, y_test.max()], "r--", alpha=0.5, linewidth=2)
    ax1.set_xlabel("Actual Income Loss Hours", fontsize=11)
    ax1.set_ylabel("Predicted Income Loss Hours", fontsize=11)
    ax1.set_title("Actual vs Predicted", fontsize=13, fontweight="bold")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    
    # Residual distribution
    residuals = y_test - y_pred
    ax2.hist(residuals, bins=50, color="#00BFA5", alpha=0.7, edgecolor="white")
    ax2.axvline(0, color="red", linestyle="--", alpha=0.5)
    ax2.set_xlabel("Residual (Actual - Predicted)", fontsize=11)
    ax2.set_ylabel("Count", fontsize=11)
    ax2.set_title("Residual Distribution", fontsize=13, fontweight="bold")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    
    plt.suptitle("Income Loss Model — Regression Diagnostics", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()
    plot_path = REPORTS_DIR / "income_loss_diagnostics.png"
    fig.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  💾 Saved to {plot_path}")
    
    # ── 5. Feature importance ───────────────────────────────
    print("\n📊 Step 5: Feature Importance")
    importances = model.feature_importances_
    sorted_idx = np.argsort(importances)
    
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(range(len(sorted_idx)), importances[sorted_idx], color="#FF7043")
    ax.set_yticks(range(len(sorted_idx)))
    ax.set_yticklabels([features[i] for i in sorted_idx], fontsize=9)
    ax.set_xlabel("Feature Importance (Gain)", fontsize=11)
    ax.set_title("Income Loss Model — Feature Importance", fontsize=14, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    importance_path = REPORTS_DIR / "income_loss_feature_importance.png"
    fig.savefig(importance_path, dpi=150)
    plt.close()
    print(f"  💾 Saved to {importance_path}")
    
    # ── 6. Save model ───────────────────────────────────────
    model_path = MODELS_DIR / "income_loss_model.pkl"
    joblib.dump(model, model_path)
    print(f"\n💾 Model saved to {model_path}")
    
    # Save metrics
    all_metrics = {**cv_metrics, **test_metrics, "features": features}
    metrics_path = REPORTS_DIR / "income_loss_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(all_metrics, f, indent=2)
    print(f"💾 Metrics saved to {metrics_path}")
    
    return model, all_metrics


if __name__ == "__main__":
    train_income_loss_model()
