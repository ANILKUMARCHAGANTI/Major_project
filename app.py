"""
Streamlit Dashboard for HAAE Model Predictions with SHAP Explainability
Allows real-time input and visualization of hydration/caloric balance predictions
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import streamlit as st
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from joblib import load
import plotly.graph_objects as go
import textwrap
import warnings
warnings.filterwarnings('ignore')

try:
    from shap_explainer import SHAPExplainer
    SHAP_AVAILABLE = True
except:
    SHAP_AVAILABLE = False

# ============================================================================
# PAGE CONFIG & SETUP
# ============================================================================
st.set_page_config(
    page_title="Hydration & Nutrition Prediction Dashboard",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏃 Athlete Hydration & Nutrition Analysis Dashboard")
st.markdown("""
This interactive dashboard predicts athlete hydration deficit and caloric balance 
using the **HAAE (Hydration-Aware Adaptive Ensemble)** model with **SHAP explainability**.
""")

# ============================================================================
# LOAD MODELS & DATA
# ============================================================================
@st.cache_resource
def load_models(model_dir="outputs/haae"):
    """Load trained HAAE ensemble models."""
    try:
        rf = load(os.path.join(model_dir, "HAAE_rf.joblib"))
        gb = load(os.path.join(model_dir, "HAAE_gb.joblib"))
        mlp = load(os.path.join(model_dir, "HAAE_mlp.joblib"))
        
        # Try to load LSTM if available
        lstm_path = os.path.join(model_dir, "HAAE_lstm.joblib")
        lstm = load(lstm_path) if os.path.exists(lstm_path) else None
        
        return {"rf": rf, "gb": gb, "mlp": mlp, "lstm": lstm}
    except Exception as e:
        st.error(f"Error loading models: {e}")
        return None

@st.cache_data
def load_metrics(metrics_path="outputs/haae/HAAE_metrics.json"):
    """Load model metrics."""
    try:
        with open(metrics_path, 'r') as f:
            return json.load(f)
    except:
        return None

@st.cache_data
def load_training_data(data_path="outputs/preprocessed.csv"):
    """Load preprocessed training data for background samples."""
    try:
        df = pd.read_csv(data_path)
        return df
    except:
        return None

# ============================================================================
# FEATURE DEFINITIONS & DEFAULTS
# ============================================================================
FEATURE_GROUPS = {
    "Sleep & Recovery": ["sleep_hours", "soreness"],
    "Environment": ["temp_c", "humidity"],
    "Session Details": ["session_mins", "intensity"],
    "Cardiovascular": ["hr_rest", "hr_avg"],
    "Performance": ["distance_km", "pace_min_per_km"],
    "Nutrition": ["calories_in", "activity_calories", "caloric_balance"],
    "Hydration": ["water_intake_L", "sweat_loss_L"],
    "Physiology": ["bmr", "vo2max", "body_mass", "fatigue_score"]
}

DEFAULT_VALUES = {
    "sleep_hours": 8.0,
    "soreness": 3.0,
    "temp_c": 25.0,
    "humidity": 0.65,
    "session_mins": 60,
    "intensity": 7,
    "hr_rest": 60,
    "hr_avg": 140,
    "distance_km": 10.0,
    "pace_min_per_km": 6.0,
    "calories_in": 2500,
    "activity_calories": 800,
    "caloric_balance": -300,
    "water_intake_L": 2.5,
    "sweat_loss_L": 2.0,
    "bmr": 1700,
    "vo2max": 50,
    "body_mass": 75,
    "fatigue_score": 5.0
}

# ============================================================================
# SIDEBAR - MODEL SELECTION & DATA LOADING
# ============================================================================
st.sidebar.header("⚙️ Configuration")

# Load data
training_df = load_training_data()
models = load_models()
metrics = load_metrics()
history_df = None

if models and training_df is not None:
    st.sidebar.success("✅ Models & data loaded successfully!")
else:
    st.sidebar.error("❌ Could not load models or data. Please ensure outputs/haae/ exists.")

if metrics:
    r2 = metrics.get("R2") if isinstance(metrics, dict) else None
    rmse = metrics.get("RMSE") if isinstance(metrics, dict) else None
    r2_val = f"{r2:.4f}" if isinstance(r2, (int, float, np.floating)) else "N/A"
    rmse_val = f"{rmse:.4f}" if isinstance(rmse, (int, float, np.floating)) else "N/A"
    st.sidebar.metric("Model R² Score", r2_val)
    st.sidebar.metric("Model RMSE", rmse_val)
else:
    st.sidebar.info("Run the training pipeline to populate performance metrics.")

uploaded_history = st.sidebar.file_uploader("📥 Upload athlete history CSV", type=["csv"])
if uploaded_history is not None:
    try:
        history_df = pd.read_csv(uploaded_history)
        st.sidebar.success("History file loaded")
    except Exception as err:
        history_df = None
        st.sidebar.error(f"Unable to parse history file: {err}")

# ============================================================================
# MAIN INTERFACE - INPUT SECTION
# ============================================================================
st.header("📋 Athlete Daily Log Input")

# Create two-column layout for input
col1, col2 = st.columns(2)

athlete_input = {}

# Dynamic input fields based on FEATURE_GROUPS
for group_name, features in FEATURE_GROUPS.items():
    st.subheader(f"📌 {group_name}")
    cols = st.columns(2)
    
    for idx, feature in enumerate(features):
        col = cols[idx % 2]
        default_val = float(DEFAULT_VALUES.get(feature, 0.0))
        
        athlete_input[feature] = col.number_input(
            feature.replace("_", " ").title(),
            value=default_val,
            step=0.1,
            key=f"input_{feature}"
        )

# ============================================================================
# PREDICTION SECTION
# ============================================================================
st.header("🎯 Predictions & Analysis")

if models and training_df is not None:
    # Prepare input data
    from preprocess import select_features, engineer

    train_features = select_features(training_df, target_cols=["hydration_deficit_pct"])
    
    # Create single-row dataframe
    input_df = pd.DataFrame([athlete_input])
    input_df = engineer(input_df, target_cols=["hydration_deficit_pct"])

    # Ensure all training features exist for inference (fill missing with 0)
    missing_feats = [f for f in train_features if f not in input_df.columns]
    for col in missing_feats:
        input_df[col] = 0.0

    X_input = input_df.reindex(columns=train_features, fill_value=0.0).values

    # Ensure loaded models expect the same feature dimensionality
    expected_counts = {}
    for name, mdl in models.items():
        if mdl is None:
            continue
        expected = getattr(mdl, "n_features_in_", None)
        if expected is None and hasattr(mdl, "steps"):
            # Pipeline: look at final estimator if needed
            try:
                expected = getattr(mdl[-1], "n_features_in_", None)
            except Exception:
                expected = None
        if expected is not None:
            expected_counts[name] = expected

    mismatched = [f"{name} ({expected})" for name, expected in expected_counts.items() if expected != X_input.shape[1]]
    if mismatched:
        st.error(
            "Model artifacts are out of date. Please rerun the training pipeline so saved models "
            f"match the current feature set. Expected feature counts: {', '.join(mismatched)}; "
            f"provided sample has {X_input.shape[1]} features."
        )
        st.stop()
    
    # Make predictions with individual models and clamp to physiologic bounds
    clip_bounds = (-30.0, 80.0)

    pred_rf_raw = float(models["rf"].predict(X_input)[0])
    pred_gb_raw = float(models["gb"].predict(X_input)[0])
    pred_mlp_raw = float(models["mlp"].predict(X_input)[0])

    pred_rf = float(np.clip(pred_rf_raw, *clip_bounds))
    pred_gb = float(np.clip(pred_gb_raw, *clip_bounds))
    pred_mlp = float(np.clip(pred_mlp_raw, *clip_bounds))
    
    # Ensemble prediction: reproduce HAAE combination (contextual + global weights)
    # Compute physiologic drivers used in training
    hgap = float(input_df["sweat_loss_L"].iloc[0] - input_df["water_intake_L"].iloc[0])
    cbal = float(input_df["caloric_balance"].iloc[0])

    # Build per-model prediction vector P (n_models=3 here — RF, GB, MLP)
    P = np.array([pred_rf, pred_gb, pred_mlp])

    # Local/contextual (physio) weights - mirror logic from training
    w_rf = 0.4 + 0.3 * (hgap > 0)
    w_gb = 0.3 + 0.2 * (cbal < 0)
    w_mlp = 0.3 + 0.2 * ((abs(cbal) > 300) or (hgap > 10))
    W_local = np.array([w_rf, w_gb, w_mlp])
    W_local = W_local / (W_local.sum() + 1e-9)

    # Load global weights saved during HAAE training (fallback to uniform)
    gw_path = os.path.join("outputs", "haae", "HAAE_weights.json")
    try:
        with open(gw_path, 'r') as f:
            gw = json.load(f).get('global_weights', None)
        if gw is None or len(gw) < 3:
            gw = [1.0/3] * 3
        gw = np.array(gw[:3])
        gw = gw / (gw.sum() + 1e-9)
    except Exception:
        gw = np.array([1.0/3, 1.0/3, 1.0/3])

    # Combine contextual and global-weighted predictions (same 50/50 blending as training)
    pred_contextual = (P * W_local).sum()
    pred_global = P.dot(gw)
    pred_ensemble = 0.5 * pred_contextual + 0.5 * pred_global
    pred_ensemble = float(np.clip(pred_ensemble, *clip_bounds))
    
    # Display predictions
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("RF Prediction", f"{pred_rf:.2f}%")
    col2.metric("GB Prediction", f"{pred_gb:.2f}%")
    col3.metric("MLP Prediction", f"{pred_mlp:.2f}%")
    col4.metric("Ensemble (HAAE)", f"{pred_ensemble:.2f}%", delta=None)
    
    # Color code based on risk
    if pred_ensemble > 10:
        st.warning("⚠️ **HIGH DEHYDRATION RISK** - Immediate hydration recommended!")
    elif pred_ensemble > 5:
        st.info("ℹ️ **MODERATE DEHYDRATION RISK** - Increase fluid intake.")
    else:
        st.success("✅ **LOW DEHYDRATION RISK** - Athlete is well-hydrated.")

    # ====================================================================
    # RISK GAUGE & TREND VISUALIZATION
    # ====================================================================
    st.subheader("📊 Hydration Risk Overview")

    gauge_fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=float(pred_ensemble),
        number={"suffix": "%"},
        gauge={
            "axis": {"range": [0, 30]},
            "bar": {"color": "#FF4B4B" if pred_ensemble > 10 else ("#FFB347" if pred_ensemble > 5 else "#3DD56D")},
            "steps": [
                {"range": [0, 5], "color": "#E5F8E8"},
                {"range": [5, 10], "color": "#FFF3CD"},
                {"range": [10, 30], "color": "#F8D7DA"},
            ],
        },
        title={"text": "Real-time Hydration Deficit Risk"}
    ))
    st.plotly_chart(gauge_fig, use_container_width=True)

    # ====================================================================
    # PERSONALIZED RECOMMENDATIONS
    # ====================================================================
    st.subheader("🧭 Personalized Recommendations")
    recommendations = []

    if pred_ensemble > 10:
        recommendations.append("Increase fluid intake immediately (≥1.0 L in next hour) and consider electrolyte supplementation.")
    elif pred_ensemble > 5:
        recommendations.append("Schedule a hydration break soon and monitor sweat loss during the next session.")
    else:
        recommendations.append("Hydration status is optimal — maintain current intake patterns.")

    caloric_balance_input = athlete_input.get("caloric_balance", 0)
    if caloric_balance_input < -300:
        recommendations.append("Caloric deficit detected — add a nutrient-dense recovery meal (≈400 kcal).")
    elif caloric_balance_input > 200:
        recommendations.append("Slight caloric surplus — balance intake with planned workload to avoid fatigue.")

    sleep_hours = athlete_input.get("sleep_hours", 8)
    if sleep_hours < 7:
        recommendations.append("Aim for at least 7.5 hours of sleep tonight to aid recovery.")

    fatigue_score = athlete_input.get("fatigue_score", 5)
    if fatigue_score > 6:
        recommendations.append("High fatigue reported — reduce next session intensity or add active recovery.")

    for rec in recommendations:
        st.markdown(f"- {rec}")

    # ====================================================================
    # ATHLETE HISTORY VISUALIZATION
    # ====================================================================
    st.subheader("📚 Athlete History Insights")
    if history_df is not None:
        cols_available = history_df.columns
        hist_cols = [c for c in ["date", "hydration_deficit_pct", "water_intake_L", "sweat_loss_L", "caloric_balance"] if c in cols_available]
        if not hist_cols:
            st.warning("Uploaded history lacks expected columns like `hydration_deficit_pct` or `water_intake_L`.")
        else:
            if "date" in history_df.columns:
                history_df["date"] = pd.to_datetime(history_df["date"], errors="coerce")
                history_df.sort_values("date", inplace=True)
            st.dataframe(history_df[hist_cols].tail(50), use_container_width=True)

            if {"water_intake_L", "sweat_loss_L"}.issubset(history_df.columns):
                balance_fig = go.Figure()
                balance_fig.add_trace(go.Scatter(x=history_df["date"] if "date" in history_df.columns else np.arange(len(history_df)),
                                                 y=history_df["water_intake_L"], mode="lines", name="Water Intake (L)", line=dict(color="#1f77b4")))
                balance_fig.add_trace(go.Scatter(x=history_df["date"] if "date" in history_df.columns else np.arange(len(history_df)),
                                                 y=history_df["sweat_loss_L"], mode="lines", name="Sweat Loss (L)", line=dict(color="#ff7f0e")))
                balance_fig.update_layout(title="Hydration Balance Over Time",
                                          xaxis_title="Date" if "date" in history_df.columns else "Session",
                                          yaxis_title="Volume (L)")
                st.plotly_chart(balance_fig, use_container_width=True)
    else:
        st.caption("Upload an athlete history CSV to unlock detailed insights.")

    # ====================================================================
    # DEBUG: expose raw inputs, features and per-model outputs, and save row
    # ====================================================================
    try:
        st.subheader("🛠️ Debug: Raw Inputs & Model Outputs")
        st.write("Raw widget inputs:", athlete_input)

        # Convert X_input (ndarray) to DataFrame for clearer display
        try:
            X_df = pd.DataFrame(X_input, columns=train_features)
        except Exception:
            X_df = pd.DataFrame(X_input)

        st.write("Preprocessed feature vector used for prediction:")
        st.dataframe(X_df.T, use_container_width=True)

        st.write("Per-model raw predictions (no scaling/clipping):")
        raw_preds = {
            "RF_raw": pred_rf_raw,
            "GB_raw": pred_gb_raw,
            "MLP_raw": pred_mlp_raw,
            "Ensemble_raw": 0.5 * (np.array([pred_rf_raw, pred_gb_raw, pred_mlp_raw]) * W_local).sum()
            + 0.5 * np.array([pred_rf_raw, pred_gb_raw, pred_mlp_raw]).dot(gw)
        }
        clipped_preds = {
            "RF_clipped": pred_rf,
            "GB_clipped": pred_gb,
            "MLP_clipped": pred_mlp,
            "Ensemble_clipped": pred_ensemble
        }
        st.json(raw_preds)
        st.json(clipped_preds)

        # Save debug row for traceability
        debug_row = {**{f"input_{k}": v for k, v in athlete_input.items()}, **raw_preds, **clipped_preds}
        debug_path = os.path.join("outputs", "debug_predictions.csv")
        write_header = not os.path.exists(debug_path)
        import csv
        with open(debug_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(debug_row.keys()))
            if write_header:
                writer.writeheader()
            writer.writerow(debug_row)

        st.caption(f"Saved debug row to `{debug_path}`")
    except Exception as e:
        st.warning(f"Debug logging failed: {e}")
    
    # ====================================================================
    # SHAP EXPLAINABILITY
    # ====================================================================
    st.header("🔍 SHAP Feature Importance Analysis")
    
    if SHAP_AVAILABLE:
        try:
            # Initialize SHAP explainer with training data
            sample_background = training_df[train_features].values[:100]
            explainer = SHAPExplainer(models["gb"], sample_background, train_features)
            
            # Get explanation for this prediction
            explanation = explainer.explain_prediction(X_input, 0)
            
            if "error" not in explanation:
                # Create visualization of feature contributions
                shap_vals = np.array(explanation["shap_values"])
                feature_vals = X_input[0]
                
                # Sort by absolute SHAP value
                sorted_idx = np.argsort(np.abs(shap_vals))[-10:]  # Top 10 features
                
                fig, ax = plt.subplots(figsize=(10, 6))
                
                # Create horizontal bar plot
                y_pos = np.arange(len(sorted_idx))
                colors = ['red' if v < 0 else 'green' for v in shap_vals[sorted_idx]]
                
                ax.barh(y_pos, shap_vals[sorted_idx], color=colors, alpha=0.7)
                ax.set_yticks(y_pos)
                ax.set_yticklabels([train_features[i] for i in sorted_idx])
                ax.set_xlabel("SHAP Value (Impact on Prediction)")
                ax.set_title("Top 10 Features Influencing Hydration Prediction")
                ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
                
                st.pyplot(fig)
                
                # Display detailed explanation
                st.subheader("📊 Feature Contribution Details")
                
                explanation_df = pd.DataFrame({
                    'Feature': train_features,
                    'Value': feature_vals,
                    'SHAP Contribution': shap_vals
                }).sort_values('SHAP Contribution', key=abs, ascending=False).head(10)
                
                st.dataframe(explanation_df, use_container_width=True)
                
                # Model base value (expected prediction)
                st.info(f"📌 **Base Model Prediction**: {explanation['base_value']:.2f}%")
                
        except Exception as e:
            st.warning(f"Could not generate SHAP explanations: {e}")
    else:
        st.info("💡 Install SHAP (`pip install shap`) to see feature importance analysis.")
    
    # ====================================================================
    # COMPARISON WITH HISTORICAL DATA
    # ====================================================================
    st.header("📈 Comparison with Training Distribution")
    
    col1, col2 = st.columns(2)
    
    # Hydration deficit distribution
    with col1:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.hist(training_df["hydration_deficit_pct"], bins=30, alpha=0.7, label="Training Data")
        ax.axvline(pred_ensemble, color='red', linestyle='--', linewidth=2, label="This Prediction")
        ax.set_xlabel("Hydration Deficit (%)")
        ax.set_ylabel("Frequency")
        ax.set_title("Hydration Deficit Distribution")
        ax.legend()
        st.pyplot(fig)
    
    # Caloric balance distribution
    with col2:
        fig, ax = plt.subplots(figsize=(10, 5))
        caloric_balance = athlete_input.get("caloric_balance", 0)
        ax.hist(training_df["caloric_balance"], bins=30, alpha=0.7, label="Training Data")
        ax.axvline(caloric_balance, color='blue', linestyle='--', linewidth=2, label="This Prediction")
        ax.set_xlabel("Caloric Balance (kcal)")
        ax.set_ylabel("Frequency")
        ax.set_title("Caloric Balance Distribution")
        ax.legend()
        st.pyplot(fig)

else:
    st.error("Could not load models. Please ensure the pipeline has been run successfully.")

# ============================================================================
# SUMMARY REPORT GENERATION
# ============================================================================
st.sidebar.markdown("---")
st.sidebar.header("📝 Reports")

def build_summary_text(pred_value, recommendations_list):
    wrapped_recs = "\n".join(["• " + textwrap.fill(rec, width=90) for rec in recommendations_list])
    report_lines = [
        f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Predicted Hydration Deficit: {pred_value:.2f}%",
        "Recommendations:",
        wrapped_recs if wrapped_recs else "• Maintain current routine",
    ]
    return "\n".join(report_lines)

def generate_pdf_report(summary_text):
    buffer = BytesIO()
    with PdfPages(buffer) as pdf:
        fig, ax = plt.subplots(figsize=(8.27, 11.69))
        ax.axis('off')
        ax.text(0, 1, "Hydration & Nutrition Summary", fontsize=16, fontweight='bold', va='top')
        ax.text(0, 0.95, summary_text, fontsize=12, va='top')
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    buffer.seek(0)
    return buffer

def generate_html_report(summary_text):
    html_content = f"""
    <html>
    <head><title>Hydration & Nutrition Summary</title></head>
    <body>
    <h2>Hydration & Nutrition Summary</h2>
    <pre style='font-size:14px;'>{summary_text}</pre>
    </body>
    </html>
    """
    return html_content

if models and training_df is not None:
    summary_text = build_summary_text(pred_ensemble if 'pred_ensemble' in locals() else 0.0, recommendations if 'recommendations' in locals() else [])
    pdf_buffer = generate_pdf_report(summary_text)
    html_content = generate_html_report(summary_text)

    st.sidebar.download_button(
        label="⬇️ Download PDF Summary",
        data=pdf_buffer,
        file_name="hydration_summary.pdf",
        mime="application/pdf",
    )

    st.sidebar.download_button(
        label="⬇️ Download HTML Summary",
        data=html_content,
        file_name="hydration_summary.html",
        mime="text/html",
    )

# ============================================================================
# FOOTER & DEPLOYMENT INFO
# ============================================================================
st.divider()
st.markdown("""
### 📚 Model Information
- **Algorithm**: HAAE (Hydration-Aware Adaptive Ensemble)
- **Base Learners**: Random Forest, Gradient Boosting, MLP, LSTM
- **Explainability**: SHAP (SHapley Additive exPlanations)
""")

st.sidebar.markdown("---")
st.sidebar.markdown("**Nutrition & Hydration Pipeline Plus** | v1.0")
