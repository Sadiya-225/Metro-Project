"""
Statistical Significance Analysis
==================================
Paired t-tests, Wilcoxon signed-rank tests, effect sizes, confidence intervals
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple
from scipy import stats


class StatisticalComparison:
    """Compare ML models using statistical tests."""

    @staticmethod
    def paired_t_test(y_true: np.ndarray, y_pred_a: np.ndarray, y_pred_b: np.ndarray) -> Dict:
        """
        Paired t-test comparing prediction errors of two models.

        Args:
            y_true: True target values
            y_pred_a: Predictions from model A
            y_pred_b: Predictions from model B

        Returns:
            Dictionary with test results
        """
        # Calculate absolute errors
        errors_a = np.abs(y_true - y_pred_a)
        errors_b = np.abs(y_true - y_pred_b)

        # Paired t-test
        t_stat, p_value = stats.ttest_rel(errors_a, errors_b)

        return {
            "test": "Paired t-test",
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "significant_alpha_0.05": p_value < 0.05,
            "mean_error_a": float(errors_a.mean()),
            "mean_error_b": float(errors_b.mean()),
            "std_error_a": float(errors_a.std()),
            "std_error_b": float(errors_b.std()),
            "difference_mean": float((errors_a - errors_b).mean()),
        }

    @staticmethod
    def wilcoxon_test(y_true: np.ndarray, y_pred_a: np.ndarray, y_pred_b: np.ndarray) -> Dict:
        """
        Wilcoxon signed-rank test (non-parametric alternative to paired t-test).

        Args:
            y_true: True target values
            y_pred_a: Predictions from model A
            y_pred_b: Predictions from model B

        Returns:
            Dictionary with test results
        """
        # Calculate absolute errors
        errors_a = np.abs(y_true - y_pred_a)
        errors_b = np.abs(y_true - y_pred_b)

        # Wilcoxon signed-rank test
        statistic, p_value = stats.wilcoxon(errors_a, errors_b)

        return {
            "test": "Wilcoxon Signed-Rank",
            "statistic": float(statistic),
            "p_value": float(p_value),
            "significant_alpha_0.05": p_value < 0.05,
            "median_error_a": float(np.median(errors_a)),
            "median_error_b": float(np.median(errors_b)),
            "note": "Non-parametric test, more robust to outliers"
        }

    @staticmethod
    def effect_size_cohens_d(y_true: np.ndarray, y_pred_a: np.ndarray, y_pred_b: np.ndarray) -> Dict:
        """
        Calculate Cohen's d effect size.

        Args:
            y_true: True target values
            y_pred_a: Predictions from model A
            y_pred_b: Predictions from model B

        Returns:
            Dictionary with effect size results
        """
        # Calculate absolute errors
        errors_a = np.abs(y_true - y_pred_a)
        errors_b = np.abs(y_true - y_pred_b)

        # Cohen's d
        mean_diff = errors_a.mean() - errors_b.mean()
        n1, n2 = len(errors_a), len(errors_b)
        var1, var2 = errors_a.var(), errors_b.var()

        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        cohens_d = mean_diff / pooled_std if pooled_std != 0 else 0

        # Interpretation
        if abs(cohens_d) < 0.2:
            interpretation = "negligible"
        elif abs(cohens_d) < 0.5:
            interpretation = "small"
        elif abs(cohens_d) < 0.8:
            interpretation = "medium"
        else:
            interpretation = "large"

        return {
            "cohens_d": float(cohens_d),
            "interpretation": interpretation,
            "effect_size_magnitude": {
                "negligible": abs(cohens_d) < 0.2,
                "small": 0.2 <= abs(cohens_d) < 0.5,
                "medium": 0.5 <= abs(cohens_d) < 0.8,
                "large": abs(cohens_d) >= 0.8,
            }
        }

    @staticmethod
    def confidence_interval(y_true: np.ndarray, y_pred: np.ndarray, confidence: float = 0.95) -> Dict:
        """
        Calculate confidence interval for MAE.

        Args:
            y_true: True target values
            y_pred: Predictions
            confidence: Confidence level (default 0.95 = 95%)

        Returns:
            Dictionary with CI results
        """
        errors = np.abs(y_true - y_pred)
        mae = errors.mean()
        std = errors.std()
        n = len(errors)

        # t-critical value
        alpha = 1 - confidence
        t_crit = stats.t.ppf(1 - alpha / 2, n - 1)

        # Margin of error
        margin = t_crit * (std / np.sqrt(n))

        return {
            "mean_absolute_error": float(mae),
            "lower_bound": float(mae - margin),
            "upper_bound": float(mae + margin),
            "confidence_level": confidence,
            "standard_error": float(std / np.sqrt(n)),
            "sample_size": n,
        }

    @staticmethod
    def bootstrap_ci(y_true: np.ndarray, y_pred: np.ndarray, n_bootstrap: int = 1000, confidence: float = 0.95) -> Dict:
        """
        Calculate bootstrap confidence interval for MAE.

        Args:
            y_true: True target values
            y_pred: Predictions
            n_bootstrap: Number of bootstrap samples
            confidence: Confidence level

        Returns:
            Dictionary with bootstrap CI results
        """
        errors = np.abs(y_true - y_pred)
        mae = errors.mean()

        # Bootstrap resampling
        bootstrap_maes = []
        np.random.seed(42)
        for _ in range(n_bootstrap):
            indices = np.random.choice(len(errors), size=len(errors), replace=True)
            bootstrap_mae = errors[indices].mean()
            bootstrap_maes.append(bootstrap_mae)

        bootstrap_maes = np.array(bootstrap_maes)

        # Percentile method
        alpha = 1 - confidence
        lower_percentile = alpha / 2 * 100
        upper_percentile = (1 - alpha / 2) * 100

        lower_ci = np.percentile(bootstrap_maes, lower_percentile)
        upper_ci = np.percentile(bootstrap_maes, upper_percentile)

        return {
            "mean_absolute_error": float(mae),
            "bootstrap_lower_bound": float(lower_ci),
            "bootstrap_upper_bound": float(upper_ci),
            "bootstrap_samples": n_bootstrap,
            "confidence_level": confidence,
            "bootstrap_std": float(bootstrap_maes.std()),
        }

    @staticmethod
    def compare_models(
        y_true: np.ndarray,
        predictions: Dict[str, np.ndarray],
        model_names: Tuple[str, str]
    ) -> Dict:
        """
        Compare two models using multiple statistical tests.

        Args:
            y_true: True target values
            predictions: Dictionary mapping model names to their predictions
            model_names: Tuple of (model_a_name, model_b_name)

        Returns:
            Comprehensive comparison results
        """
        model_a, model_b = model_names
        y_pred_a = predictions[model_a]
        y_pred_b = predictions[model_b]

        comparison = {
            "comparison": f"{model_a} vs {model_b}",
            "samples": len(y_true),
            "paired_t_test": StatisticalComparison.paired_t_test(y_true, y_pred_a, y_pred_b),
            "wilcoxon_test": StatisticalComparison.wilcoxon_test(y_true, y_pred_a, y_pred_b),
            "effect_size": StatisticalComparison.effect_size_cohens_d(y_true, y_pred_a, y_pred_b),
            "confidence_intervals": {
                model_a: StatisticalComparison.confidence_interval(y_true, y_pred_a),
                model_b: StatisticalComparison.confidence_interval(y_true, y_pred_b),
            },
            "bootstrap_ci": {
                model_a: StatisticalComparison.bootstrap_ci(y_true, y_pred_a),
                model_b: StatisticalComparison.bootstrap_ci(y_true, y_pred_b),
            }
        }

        return comparison


class RobustnessAnalyzer:
    """Analyze model robustness metrics."""

    @staticmethod
    def sensitivity_analysis(y_pred_nominal: np.ndarray, y_pred_perturbed: np.ndarray) -> Dict:
        """
        Analyze sensitivity to input perturbations.

        Args:
            y_pred_nominal: Predictions with nominal inputs
            y_pred_perturbed: Predictions with perturbed inputs

        Returns:
            Sensitivity metrics
        """
        prediction_change = np.abs(y_pred_nominal - y_pred_perturbed)

        return {
            "mean_prediction_change": float(prediction_change.mean()),
            "std_prediction_change": float(prediction_change.std()),
            "max_prediction_change": float(prediction_change.max()),
            "percentage_change": float((prediction_change / np.abs(y_pred_nominal + 1e-6)).mean() * 100),
        }

    @staticmethod
    def stability_under_noise(y_true: np.ndarray, y_pred: np.ndarray, noise_levels: list = None) -> Dict:
        """
        Test prediction stability under input noise.

        Args:
            y_true: True values
            y_pred: Predictions
            noise_levels: List of noise standard deviations to test

        Returns:
            Stability analysis results
        """
        if noise_levels is None:
            noise_levels = [0.01, 0.05, 0.1, 0.2]

        results = {
            "nominal_mae": float(np.mean(np.abs(y_true - y_pred))),
            "noise_robustness": {}
        }

        np.random.seed(42)
        for noise_level in noise_levels:
            # Add noise to predictions
            y_pred_noisy = y_pred + np.random.normal(0, noise_level, size=y_pred.shape)

            # Calculate degradation
            mae_noisy = np.mean(np.abs(y_true - y_pred_noisy))
            degradation = (mae_noisy - results["nominal_mae"]) / results["nominal_mae"] * 100

            results["noise_robustness"][f"noise_std_{noise_level}"] = {
                "mae": float(mae_noisy),
                "degradation_percent": float(degradation),
            }

        return results
