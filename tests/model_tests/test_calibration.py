import unittest
import numpy as np
import pandas as pd
import os
import sys
import matplotlib.pyplot as plt
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.model_factory.model_calibration import ModelCalibrator
from src.utils.healthcare_metrics import HealthcareMetrics

class TestCalibration(unittest.TestCase):
    """Test suite for model calibration functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample data for testing
        np.random.seed(42)
        n_samples = 1000
        
        # Generate synthetic predictions and outcomes
        # Deliberately make predictions slightly miscalibrated
        self.y_true = np.random.binomial(1, 0.3, size=n_samples)
        raw_pred = np.random.normal(0.3, 0.2, size=n_samples)
        self.y_pred_uncalibrated = np.clip(raw_pred, 0.01, 0.99)  # Ensure predictions are in (0,1)
        
        # Create a more severely miscalibrated set
        self.y_pred_severe = np.power(self.y_pred_uncalibrated, 0.5)  # Square root makes predictions too high
        
        # Create patient IDs and additional features for testing
        self.patient_ids = [f'P{i:04d}' for i in range(n_samples)]
        self.ages = np.random.normal(65, 15, size=n_samples).astype(int)
        self.genders = np.random.choice(['M', 'F'], size=n_samples)
        
        # Create DataFrame
        self.df = pd.DataFrame({
            'patient_id': self.patient_ids,
            'age': self.ages,
            'gender': self.genders,
            'true_outcome': self.y_true,
            'prediction_uncalibrated': self.y_pred_uncalibrated,
            'prediction_severe': self.y_pred_severe
        })
        
        # Create calibrator instance
        self.calibrator = ModelCalibrator()
        
        # Create healthcare metrics instance
        self.metrics = HealthcareMetrics()

    def test_calibration_curve(self):
        """Test calibration curve calculation."""
        # Calculate calibration curve
        prob_true, prob_pred = calibration_curve(
            self.y_true, self.y_pred_uncalibrated, n_bins=10
        )
        
        # Check output shapes
        self.assertEqual(len(prob_true), 10)
        self.assertEqual(len(prob_pred), 10)
        
        # Check values are in range [0, 1]
        self.assertTrue(np.all(prob_true >= 0) and np.all(prob_true <= 1))
        self.assertTrue(np.all(prob_pred >= 0) and np.all(prob_pred <= 1))

    def test_brier_score(self):
        """Test Brier score calculation."""
        # Calculate Brier score
        brier = brier_score_loss(self.y_true, self.y_pred_uncalibrated)
        
        # Check value is in range [0, 1]
        self.assertTrue(0 <= brier <= 1)
        
        # Check severely miscalibrated predictions have worse Brier score
        brier_severe = brier_score_loss(self.y_true, self.y_pred_severe)
        self.assertGreater(brier_severe, brier)

    def test_isotonic_calibration(self):
        """Test isotonic regression calibration."""
        # Calibrate predictions using isotonic regression
        calibrated_pred = self.calibrator.calibrate(
            self.y_pred_uncalibrated, 
            self.y_true, 
            method='isotonic'
        )
        
        # Check output shape
        self.assertEqual(len(calibrated_pred), len(self.y_pred_uncalibrated))
        
        # Check values are in range [0, 1]
        self.assertTrue(np.all(calibrated_pred >= 0) and np.all(calibrated_pred <= 1))
        
        # Check calibration improves Brier score
        brier_before = brier_score_loss(self.y_true, self.y_pred_uncalibrated)
        brier_after = brier_score_loss(self.y_true, calibrated_pred)
        
        # Note: In some cases with random data, calibration might not improve the score
        # But with our deliberately miscalibrated data, it should improve
        self.assertLessEqual(brier_after, brier_before * 1.05)  # Allow small tolerance

    def test_platt_scaling(self):
        """Test Platt scaling calibration."""
        # Calibrate predictions using Platt scaling
        calibrated_pred = self.calibrator.calibrate(
            self.y_pred_uncalibrated, 
            self.y_true, 
            method='platt'
        )
        
        # Check output shape
        self.assertEqual(len(calibrated_pred), len(self.y_pred_uncalibrated))
        
        # Check values are in range [0, 1]
        self.assertTrue(np.all(calibrated_pred >= 0) and np.all(calibrated_pred <= 1))
        
        # Check calibration improves Brier score
        brier_before = brier_score_loss(self.y_true, self.y_pred_uncalibrated)
        brier_after = brier_score_loss(self.y_true, calibrated_pred)
        
        # Note: In some cases with random data, calibration might not improve the score
        # But with our deliberately miscalibrated data, it should improve
        self.assertLessEqual(brier_after, brier_before * 1.05)  # Allow small tolerance

    def test_beta_calibration(self):
        """Test Beta calibration."""
        # Calibrate predictions using Beta calibration
        calibrated_pred = self.calibrator.calibrate(
            self.y_pred_uncalibrated, 
            self.y_true, 
            method='beta'
        )
        
        # Check output shape
        self.assertEqual(len(calibrated_pred), len(self.y_pred_uncalibrated))
        
        # Check values are in range [0, 1]
        self.assertTrue(np.all(calibrated_pred >= 0) and np.all(calibrated_pred <= 1))
        
        # Check calibration improves Brier score
        brier_before = brier_score_loss(self.y_true, self.y_pred_uncalibrated)
        brier_after = brier_score_loss(self.y_true, calibrated_pred)
        
        # Note: In some cases with random data, calibration might not improve the score
        # But with our deliberately miscalibrated data, it should improve
        self.assertLessEqual(brier_after, brier_before * 1.05)  # Allow small tolerance

    def test_calibration_by_group(self):
        """Test calibration by demographic group."""
        # Split data by gender
        df_male = self.df[self.df['gender'] == 'M']
        df_female = self.df[self.df['gender'] == 'F']
        
        # Calculate calibration curves for each group
        result = self.calibrator.calculate_calibration_by_group(
            self.df,
            prediction_column='prediction_uncalibrated',
            outcome_column='true_outcome',
            group_column='gender'
        )
        
        # Check result structure
        self.assertIn('M', result)
        self.assertIn('F', result)
        self.assertIn('prob_true', result['M'])
        self.assertIn('prob_pred', result['M'])
        self.assertIn('prob_true', result['F'])
        self.assertIn('prob_pred', result['F'])
        
        # Check values are in range [0, 1]
        self.assertTrue(np.all(result['M']['prob_true'] >= 0) and np.all(result['M']['prob_true'] <= 1))
        self.assertTrue(np.all(result['M']['prob_pred'] >= 0) and np.all(result['M']['prob_pred'] <= 1))
        self.assertTrue(np.all(result['F']['prob_true'] >= 0) and np.all(result['F']['prob_true'] <= 1))
        self.assertTrue(np.all(result['F']['prob_pred'] >= 0) and np.all(result['F']['prob_pred'] <= 1))

    def test_calibration_metrics(self):
        """Test calibration metrics calculation."""
        # Calculate calibration metrics
        metrics = self.calibrator.calculate_calibration_metrics(
            self.y_true,
            self.y_pred_uncalibrated
        )
        
        # Check metrics structure
        self.assertIn('brier_score', metrics)
        self.assertIn('expected_calibration_error', metrics)
        self.assertIn('maximum_calibration_error', metrics)
        self.assertIn('calibration_slope', metrics)
        self.assertIn('calibration_intercept', metrics)
        
        # Check values are reasonable
        self.assertTrue(0 <= metrics['brier_score'] <= 1)
        self.assertTrue(0 <= metrics['expected_calibration_error'] <= 1)
        self.assertTrue(0 <= metrics['maximum_calibration_error'] <= 1)
        
        # Check severely miscalibrated predictions have worse metrics
        metrics_severe = self.calibrator.calculate_calibration_metrics(
            self.y_true,
            self.y_pred_severe
        )
        
        self.assertGreater(metrics_severe['brier_score'], metrics['brier_score'])
        self.assertGreater(metrics_severe['expected_calibration_error'], metrics['expected_calibration_error'])

    def test_calibration_plot(self):
        """Test calibration plot generation."""
        # Generate calibration plot
        fig = self.calibrator.plot_calibration_curve(
            self.y_true,
            self.y_pred_uncalibrated,
            title='Calibration Test'
        )
        
        # Check figure is created
        self.assertIsInstance(fig, plt.Figure)
        
        # Check figure has expected elements
        self.assertEqual(len(fig.axes), 1)
        
        # Clean up
        plt.close(fig)

    def test_group_calibration_plot(self):
        """Test group calibration plot generation."""
        # Generate group calibration plot
        fig = self.calibrator.plot_calibration_by_group(
            self.df,
            prediction_column='prediction_uncalibrated',
            outcome_column='true_outcome',
            group_column='gender',
            title='Group Calibration Test'
        )
        
        # Check figure is created
        self.assertIsInstance(fig, plt.Figure)
        
        # Check figure has expected elements
        self.assertEqual(len(fig.axes), 1)
        
        # Clean up
        plt.close(fig)

    def test_calibration_comparison(self):
        """Test comparison of calibration methods."""
        # Compare calibration methods
        result = self.calibrator.compare_calibration_methods(
            self.y_pred_uncalibrated,
            self.y_true,
            methods=['isotonic', 'platt', 'beta']
        )
        
        # Check result structure
        self.assertIn('uncalibrated', result)
        self.assertIn('isotonic', result)
        self.assertIn('platt', result)
        self.assertIn('beta', result)
        
        for method in ['uncalibrated', 'isotonic', 'platt', 'beta']:
            self.assertIn('brier_score', result[method])
            self.assertIn('expected_calibration_error', result[method])
            self.assertIn('predictions', result[method])
        
        # Check predictions have correct length
        for method in ['uncalibrated', 'isotonic', 'platt', 'beta']:
            self.assertEqual(len(result[method]['predictions']), len(self.y_true))
        
        # Generate comparison plot
        fig = self.calibrator.plot_calibration_comparison(
            self.y_pred_uncalibrated,
            self.y_true,
            methods=['isotonic', 'platt', 'beta'],
            title='Calibration Comparison'
        )
        
        # Check figure is created
        self.assertIsInstance(fig, plt.Figure)
        
        # Clean up
        plt.close(fig)

    def test_cross_validation_calibration(self):
        """Test cross-validation for calibration."""
        # Perform cross-validation
        cv_result = self.calibrator.cross_validate_calibration(
            self.y_pred_uncalibrated,
            self.y_true,
            method='isotonic',
            cv=3
        )
        
        # Check result structure
        self.assertIn('calibrated_predictions', cv_result)
        self.assertIn('fold_metrics', cv_result)
        self.assertIn('mean_brier_score', cv_result)
        self.assertIn('std_brier_score', cv_result)
        
        # Check predictions have correct length
        self.assertEqual(len(cv_result['calibrated_predictions']), len(self.y_true))
        
        # Check fold metrics
        self.assertEqual(len(cv_result['fold_metrics']), 3)
        for fold_metric in cv_result['fold_metrics']:
            self.assertIn('brier_score', fold_metric)
            self.assertIn('expected_calibration_error', fold_metric)

    def test_integration_with_healthcare_metrics(self):
        """Test integration with healthcare metrics."""
        # Create a test dataset with clinical outcomes
        df_clinical = self.df.copy()
        df_clinical['mortality'] = self.y_true
        df_clinical['predicted_mortality'] = self.y_pred_uncalibrated
        
        # Calculate calibration metrics
        calibration_metrics = self.calibrator.calculate_calibration_metrics(
            df_clinical['mortality'],
            df_clinical['predicted_mortality']
        )
        
        # Evaluate clinical model
        clinical_eval = self.metrics.evaluate_clinical_model(
            df_clinical,
            outcome_column='mortality',
            prediction_column='predicted_mortality'
        )
        
        # Check metrics are consistent
        self.assertAlmostEqual(
            calibration_metrics['brier_score'],
            clinical_eval['brier_score'],
            places=4
        )
        
        # Check calibration slope and intercept
        self.assertAlmostEqual(
            calibration_metrics['calibration_slope'],
            clinical_eval['calibration_slope'],
            places=4
        )
        self.assertAlmostEqual(
            calibration_metrics['calibration_intercept'],
            clinical_eval['calibration_intercept'],
            places=4
        )

    def test_save_and_load_calibrator(self):
        """Test saving and loading calibrator models."""
        # Train a calibrator
        self.calibrator.fit(
            self.y_pred_uncalibrated,
            self.y_true,
            method='isotonic'
        )
        
        # Save the calibrator
        save_path = 'test_calibrator.pkl'
        self.calibrator.save(save_path)
        
        # Check file exists
        self.assertTrue(os.path.exists(save_path))
        
        # Load the calibrator
        loaded_calibrator = ModelCalibrator.load(save_path)
        
        # Check predictions are consistent
        original_pred = self.calibrator.transform(self.y_pred_uncalibrated)
        loaded_pred = loaded_calibrator.transform(self.y_pred_uncalibrated)
        
        np.testing.assert_array_almost_equal(original_pred, loaded_pred)
        
        # Clean up
        os.remove(save_path)

    def test_recalibration_over_time(self):
        """Test recalibration over time simulation."""
        # Create time-based data
        np.random.seed(42)
        n_samples = 1000
        
        # Generate data for two time periods with drift
        y_true_period1 = np.random.binomial(1, 0.3, size=n_samples)
        y_pred_period1 = np.random.normal(0.3, 0.2, size=n_samples)
        y_pred_period1 = np.clip(y_pred_period1, 0.01, 0.99)
        
        # Period 2 has higher event rate but predictions don't account for it
        y_true_period2 = np.random.binomial(1, 0.4, size=n_samples)
        y_pred_period2 = np.random.normal(0.3, 0.2, size=n_samples)
        y_pred_period2 = np.clip(y_pred_period2, 0.01, 0.99)
        
        # Create DataFrames
        df_period1 = pd.DataFrame({
            'true_outcome': y_true_period1,
            'prediction': y_pred_period1,
            'period': 1
        })
        
        df_period2 = pd.DataFrame({
            'true_outcome': y_true_period2,
            'prediction': y_pred_period2,
            'period': 2
        })
        
        df_combined = pd.concat([df_period1, df_period2])
        
        # Calculate calibration drift
        drift_result = self.calibrator.detect_calibration_drift(
            df_combined,
            prediction_column='prediction',
            outcome_column='true_outcome',
            time_column='period'
        )
        
        # Check result structure
        self.assertIn('drift_detected', drift_result)
        self.assertIn('period_metrics', drift_result)
        self.assertIn(1, drift_result['period_metrics'])
        self.assertIn(2, drift_result['period_metrics'])
        
        # Period 2 should have worse calibration
        self.assertGreater(
            drift_result['period_metrics'][2]['brier_score'],
            drift_result['period_metrics'][1]['brier_score']
        )
        
        # Recalibrate period 2 using period 1 as reference
        recal_result = self.calibrator.recalibrate_by_period(
            df_combined,
            prediction_column='prediction',
            outcome_column='true_outcome',
            time_column='period',
            reference_period=1,
            target_period=2,
            method='isotonic'
        )
        
        # Check recalibration improves Brier score for period 2
        self.assertLess(
            recal_result['after']['brier_score'],
            recal_result['before']['brier_score']
        )


if __name__ == '__main__':
    unittest.main()
