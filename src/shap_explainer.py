"""
SHAP-based Explainability Module
Provides visual explanations for HAAE model predictions using SHAP library.
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

try:
    import shap
    SHAP_AVAILABLE = True
except:
    SHAP_AVAILABLE = False
    print("Warning: SHAP not available. Install via: pip install shap")


class SHAPExplainer:
    """
    Wrapper for SHAP explainability on ensemble models.
    Supports force plots, summary plots, and waterfall explanations.
    """
    
    def __init__(self, model, X_background, feature_names=None):
        """
        Initialize SHAP explainer.
        
        Args:
            model: Sklearn model or pipeline with predict method
            X_background: Background data for SHAP (smaller sample recommended)
            feature_names: List of feature names
        """
        self.model = model
        self.X_background = X_background
        self.feature_names = feature_names or [f"Feature_{i}" for i in range(X_background.shape[1])]
        self.explainer = None
        self.shap_values = None
        
        if SHAP_AVAILABLE:
            # Use KernelExplainer as it works with any model
            self.explainer = shap.KernelExplainer(
                model.predict, 
                shap.sample(X_background, min(100, len(X_background)))
            )
    
    def explain_prediction(self, X_sample, instance_idx=0):
        """
        Explain a single prediction using SHAP.
        
        Args:
            X_sample: Input features (single row or batch)
            instance_idx: Index of instance to explain (if batch provided)
        
        Returns:
            Dictionary with SHAP values and base value
        """
        if not SHAP_AVAILABLE:
            return {"error": "SHAP not available"}
        
        if len(X_sample.shape) == 1:
            X_sample = X_sample.reshape(1, -1)
        
        # Get SHAP values for this sample
        shap_values = self.explainer.shap_values(X_sample)
        base_value = self.explainer.expected_value
        
        if isinstance(shap_values, list):
            shap_values = shap_values[0]  # For binary/multiclass
        
        return {
            "base_value": float(base_value),
            "shap_values": shap_values[instance_idx].tolist(),
            "features": self.feature_names,
            "prediction": float(self.model.predict(X_sample)[instance_idx])
        }
    
    def force_plot(self, X_sample, instance_idx=0, save_path=None):
        """
        Generate SHAP force plot for single instance.
        
        Args:
            X_sample: Input features
            instance_idx: Index of instance to explain
            save_path: Path to save figure (optional)
        """
        if not SHAP_AVAILABLE:
            print("SHAP not available")
            return None
        
        if len(X_sample.shape) == 1:
            X_sample = X_sample.reshape(1, -1)
        
        shap_values = self.explainer.shap_values(X_sample)
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        
        try:
            # Create force plot
            plt.figure(figsize=(14, 4))
            shap.force_plot(
                self.explainer.expected_value,
                shap_values[instance_idx],
                X_sample[instance_idx],
                feature_names=self.feature_names,
                matplotlib=True,
                show=False
            )
            
            if save_path:
                plt.savefig(save_path, dpi=100, bbox_inches='tight')
                print(f"Force plot saved to {save_path}")
            
            plt.close()
            return True
        except Exception as e:
            print(f"Error creating force plot: {e}")
            return False
    
    def summary_plot(self, X_data, save_path=None, plot_type="bar"):
        """
        Generate SHAP summary plot for multiple instances.
        
        Args:
            X_data: Input features (multiple samples)
            save_path: Path to save figure (optional)
            plot_type: "bar", "beeswarm", or "violin"
        """
        if not SHAP_AVAILABLE:
            print("SHAP not available")
            return None
        
        # Sample if too many instances
        if len(X_data) > 100:
            indices = np.random.choice(len(X_data), 100, replace=False)
            X_sample = X_data[indices]
        else:
            X_sample = X_data
        
        shap_values = self.explainer.shap_values(X_sample)
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        
        try:
            plt.figure(figsize=(12, 8))
            shap.summary_plot(
                shap_values,
                X_sample,
                feature_names=self.feature_names,
                plot_type=plot_type,
                show=False
            )
            
            if save_path:
                plt.savefig(save_path, dpi=100, bbox_inches='tight')
                print(f"Summary plot saved to {save_path}")
            
            plt.close()
            return True
        except Exception as e:
            print(f"Error creating summary plot: {e}")
            return False
    
    def waterfall_plot(self, X_sample, instance_idx=0, save_path=None):
        """
        Generate SHAP waterfall plot showing contribution of each feature.
        
        Args:
            X_sample: Input features
            instance_idx: Index of instance to explain
            save_path: Path to save figure (optional)
        """
        if not SHAP_AVAILABLE:
            print("SHAP not available")
            return None
        
        if len(X_sample.shape) == 1:
            X_sample = X_sample.reshape(1, -1)
        
        shap_values = self.explainer.shap_values(X_sample)
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        
        try:
            # Create explanation object
            explanation = shap.Explanation(
                values=shap_values[instance_idx],
                base_values=self.explainer.expected_value,
                data=X_sample[instance_idx],
                feature_names=self.feature_names
            )
            
            plt.figure(figsize=(12, 8))
            shap.plots.waterfall(explanation, show=False)
            
            if save_path:
                plt.savefig(save_path, dpi=100, bbox_inches='tight')
                print(f"Waterfall plot saved to {save_path}")
            
            plt.close()
            return True
        except Exception as e:
            print(f"Error creating waterfall plot: {e}")
            return False
    
    def feature_importance_dict(self, X_data):
        """
        Compute mean absolute SHAP values for feature importance ranking.
        
        Args:
            X_data: Input features
        
        Returns:
            Dictionary of feature importance scores
        """
        if not SHAP_AVAILABLE:
            return {}
        
        # Sample if too large
        if len(X_data) > 100:
            indices = np.random.choice(len(X_data), 100, replace=False)
            X_sample = X_data[indices]
        else:
            X_sample = X_data
        
        shap_values = self.explainer.shap_values(X_sample)
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        
        # Mean absolute SHAP values
        importance = np.abs(shap_values).mean(axis=0)
        feature_importance = dict(zip(self.feature_names, importance.tolist()))
        
        # Sort by importance
        feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
        return feature_importance


def create_shap_report(model, X_train, X_test, y_test, feature_names, output_dir):
    """
    Generate a comprehensive SHAP explainability report.
    
    Args:
        model: Trained sklearn model
        X_train: Training features (for background)
        X_test: Test features
        y_test: Test targets
        feature_names: List of feature names
        output_dir: Directory to save plots and report
    """
    os.makedirs(output_dir, exist_ok=True)
    
    print("Creating SHAP explainability report...")
    
    # Initialize explainer
    explainer = SHAPExplainer(model, X_train[:200], feature_names)
    
    if not SHAP_AVAILABLE:
        print("SHAP not installed. Skipping explainability report.")
        return
    
    # 1. Summary plot (bar)
    print("  - Creating summary plot (bar)...")
    explainer.summary_plot(X_test, os.path.join(output_dir, "shap_summary_bar.png"), plot_type="bar")
    
    # 2. Summary plot (beeswarm)
    print("  - Creating summary plot (beeswarm)...")
    explainer.summary_plot(X_test, os.path.join(output_dir, "shap_summary_beeswarm.png"), plot_type="beeswarm")
    
    # 3. Feature importance JSON
    print("  - Computing feature importance...")
    feature_importance = explainer.feature_importance_dict(X_test)
    with open(os.path.join(output_dir, "shap_feature_importance.json"), "w") as f:
        json.dump(feature_importance, f, indent=2)
    
    # 4. Explain sample instances (best, worst, median)
    y_pred = model.predict(X_test)
    residuals = np.abs(y_test - y_pred)
    
    best_idx = np.argmin(residuals)
    worst_idx = np.argmax(residuals)
    median_idx = np.argsort(residuals)[len(residuals)//2]
    
    for name, idx in [("best", best_idx), ("worst", worst_idx), ("median", median_idx)]:
        print(f"  - Creating waterfall plot for {name} prediction...")
        explainer.waterfall_plot(X_test, idx, os.path.join(output_dir, f"shap_waterfall_{name}.png"))
        
        # Save explanation JSON
        explanation = explainer.explain_prediction(X_test, idx)
        with open(os.path.join(output_dir, f"shap_explanation_{name}.json"), "w") as f:
            json.dump(explanation, f, indent=2)
    
    print(f"SHAP report saved to {output_dir}")


if __name__ == "__main__":
    print("SHAP Explainer module loaded successfully!")
