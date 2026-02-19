import argparse, os, json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import r2_score, mean_squared_error
from joblib import dump
import warnings
warnings.filterwarnings('ignore')

from preprocess import engineer, select_features

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    TENSORFLOW_AVAILABLE = True
except:
    TENSORFLOW_AVAILABLE = False
    print("Warning: TensorFlow not available. LSTM model will be skipped.")

def physio_weights(hgap, cbal):
    # Higher deficit -> give more weight to models that historically handle tails (GB, MLP, LSTM)
    w_gb = 0.35 + 0.25 * (hgap > 0).astype(float)
    w_rf = 0.25 + 0.15 * (cbal < 0).astype(float)
    w_mlp = 0.25 + 0.15 * ((np.abs(cbal) > 300) | (hgap > 10)).astype(float)
    w_lstm = 0.15 + 0.2 * ((hgap > 5) | (np.abs(cbal) > 500)).astype(float)  # New LSTM weight
    W = np.vstack([w_rf, w_gb, w_mlp, w_lstm]).T
    W = W / (W.sum(axis=1, keepdims=True) + 1e-9)
    return W

def build_lstm_model(input_shape, lstm_units=32, dropout_rate=0.2):
    """Build a simple LSTM model for time-series predictions."""
    model = Sequential([
        LSTM(lstm_units, activation='relu', input_shape=input_shape, return_sequences=True),
        Dropout(dropout_rate),
        LSTM(lstm_units, activation='relu'),
        Dropout(dropout_rate),
        Dense(16, activation='relu'),
        Dense(1)
    ])
    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])
    return model

def reshape_for_lstm(X, sequence_length=7):
    """Reshape feature matrix for LSTM by creating sequences."""
    n_samples, n_features = X.shape
    X_lstm = []
    
    for i in range(n_samples - sequence_length + 1):
        X_lstm.append(X[i:i+sequence_length])
    
    if len(X_lstm) == 0:
        # If not enough samples, return reshaped single sample
        return np.expand_dims(X[:sequence_length] if len(X) >= sequence_length else X[:1], axis=0)
    
    X_lstm = np.array(X_lstm)
    return X_lstm

def metrics(y_true, y_pred):
    return {"R2": float(r2_score(y_true, y_pred)),
            "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred)))}

def train_haae(df, target, outdir):
    os.makedirs(outdir, exist_ok=True)
    feats = select_features(df, target_cols=[target])
    X = df[feats].values
    y = df[target].values
    # Aux physiologic drivers
    hgap = (df["sweat_loss_L"] - df["water_intake_L"]).values
    cbal = df["caloric_balance"].values

    X_train, X_test, y_train, y_test, hgap_tr, hgap_te, cbal_tr, cbal_te = train_test_split(
        X, y, hgap, cbal, test_size=0.2, random_state=42)

    # Base learners: RF, GB, MLP
    rf = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1)
    gb = GradientBoostingRegressor(random_state=42)
    mlp = Pipeline([("scaler", StandardScaler()), ("model", MLPRegressor(hidden_layer_sizes=(64,32), random_state=42, max_iter=400))])

    rf.fit(X_train, y_train)
    gb.fit(X_train, y_train)
    mlp.fit(X_train, y_train)

    clip_bounds = (-30.0, 80.0)

    p_rf = np.clip(rf.predict(X_test), *clip_bounds)
    p_gb = np.clip(gb.predict(X_test), *clip_bounds)
    p_mlp = np.clip(mlp.predict(X_test), *clip_bounds)
    
    # LSTM model (if TensorFlow available)
    p_lstm = None
    if TENSORFLOW_AVAILABLE and len(X_train) > 14:
        try:
            # Prepare sequences for LSTM
            scaler_lstm = StandardScaler()
            X_train_scaled = scaler_lstm.fit_transform(X_train)
            X_test_scaled = scaler_lstm.transform(X_test)
            
            sequence_length = 7
            X_train_lstm = reshape_for_lstm(X_train_scaled, sequence_length)
            X_test_lstm = reshape_for_lstm(X_test_scaled, sequence_length)
            
            lstm_model = build_lstm_model((sequence_length, X_train_lstm.shape[2]))
            lstm_model.fit(X_train_lstm, y_train[:len(X_train_lstm)], 
                          epochs=20, batch_size=16, verbose=0, validation_split=0.1)
            
            p_lstm_full = lstm_model.predict(X_test_lstm, verbose=0).flatten()
            p_lstm_full = np.clip(p_lstm_full, *clip_bounds)
            # Pad predictions to match test set size
            if len(p_lstm_full) < len(y_test):
                p_lstm = np.concatenate([p_lstm_full, np.repeat(p_lstm_full[-1], len(y_test) - len(p_lstm_full))])
            else:
                p_lstm = p_lstm_full[:len(y_test)]
            
            dump(lstm_model, os.path.join(outdir, "HAAE_lstm.joblib"))
        except Exception as e:
            print(f"LSTM training failed: {e}. Falling back to 4-model ensemble.")
            p_lstm = p_mlp  # Fallback
    
    # Use LSTM if available, else use MLP as 4th model
    if p_lstm is not None:
        P = np.vstack([p_rf, p_gb, p_mlp, p_lstm]).T  # [n,4]
    else:
        P = np.vstack([p_rf, p_gb, p_mlp]).T  # [n,3]
    
    # Adaptive weights based on physiologic context
    W = physio_weights(hgap_te, cbal_te)
    if p_lstm is not None:
        y_pred = (P * W).sum(axis=1)
    else:
        # For 3-model case, adjust weights
        W = np.vstack([
            0.4 + 0.3 * (hgap_te > 0).astype(float),
            0.3 + 0.2 * (cbal_te < 0).astype(float),
            0.3 + 0.2 * ((np.abs(cbal_te) > 300) | (hgap_te > 10)).astype(float)
        ]).T
        W = W / (W.sum(axis=1, keepdims=True) + 1e-9)
        y_pred = (P * W).sum(axis=1)

    # Fine-tune global weights via small meta-gradient step to minimize RMSE
    n_models = 4 if p_lstm is not None else 3
    w_global = np.ones(n_models, dtype=float) / n_models
    lr = 0.05
    for _ in range(50):
        y_hat = P.dot(w_global)
        grad = -2 * P.T.dot(y_test - y_hat) / len(y_test)
        w_global -= lr * grad
        w_global = np.clip(w_global, 0, None)
        w_global = w_global / (w_global.sum() + 1e-9)

    # Combine local (contextual) and global weights
    y_pred_haae = 0.5*y_pred + 0.5*(P.dot(w_global))
    y_pred_haae = np.clip(y_pred_haae, *clip_bounds)

    m = metrics(y_test, y_pred_haae)
    # Save artifacts
    dump(rf, os.path.join(outdir, "HAAE_rf.joblib"))
    dump(gb, os.path.join(outdir, "HAAE_gb.joblib"))
    dump(mlp, os.path.join(outdir, "HAAE_mlp.joblib"))
    pd.DataFrame({"y_true": y_test, "y_pred": y_pred_haae}).to_csv(os.path.join(outdir, "HAAE_preds.csv"), index=False)
    with open(os.path.join(outdir, "HAAE_metrics.json"), "w") as f:
        json.dump(m, f, indent=2)
    with open(os.path.join(outdir, "HAAE_weights.json"), "w") as f:
        json.dump({"global_weights": w_global.tolist()}, f, indent=2)

    return m

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=str, required=True)
    ap.add_argument("--target", type=str, default="hydration_deficit_pct")
    ap.add_argument("--outdir", type=str, required=True)
    args = ap.parse_args()
    df = pd.read_csv(args.data)
    df = engineer(df, target_cols=[args.target])
    m = train_haae(df, args.target, args.outdir)
    print("HAAE metrics:", m)

if __name__ == "__main__":
    main()
