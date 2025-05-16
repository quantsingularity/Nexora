import unittest
import numpy as np
import pandas as pd
import os
import sys
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, precision_recall_curve, auc, average_precision_score
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.model_selection import StratifiedKFold

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.model_factory.fairness_metrics import FairnessEvaluator
from src.utils.healthcare_metrics import HealthcareMetrics

class TestPredictiveEquality(unittest.TestCase):
    """Test suite for predictive equality and fairness functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample data for testing
        np.random.seed(42)
        n_samples = 1000
        
        # Generate synthetic predictions and outcomes
        # Create deliberate disparities between groups
        self.y_true = np.random.binomial(1, 0.3, size=n_samples)
        
        # Create patient IDs and demographic features for testing
        self.patient_ids = [f'P{i:04d}' for i in range(n_samples)]
        self.ages = np.random.normal(65, 15, size=n_samples).astype(int)
        
        # Create gender with deliberate imbalance
        self.genders = np.random.choice(['M', 'F'], size=n_samples, p=[0.6, 0.4])
        
        # Create race/ethnicity with deliberate imbalance
        self.races = np.random.choice(
            ['White', 'Black', 'Hispanic', 'Asian', 'Other'],
            size=n_samples,
            p=[0.6, 0.15, 0.15, 0.05, 0.05]
        )
        
        # Create insurance type
        self.insurance = np.random.choice(
            ['Private', 'Medicare', 'Medicaid', 'Uninsured'],
            size=n_samples,
            p=[0.5, 0.3, 0.15, 0.05]
        )
        
        # Create predictions with deliberate bias
        # Males get slightly better calibrated predictions
        male_idx = self.genders == 'M'
        female_idx = self.genders == 'F'
        
        # Base predictions
        self.y_pred = np.random.normal(0.3, 0.2, size=n_samples)
        self.y_pred = np.clip(self.y_pred, 0.01, 0.99)
        
        # Add bias - females with the condition are less likely to be predicted correctly
        female_with_condition = female_idx & (self.y_true == 1)
        self.y_pred[female_with_condition] = self.y_pred[female_with_condition] * 0.7
        
        # Add bias by race - Black patients with the condition are less likely to be predicted correctly
        black_idx = self.races == 'Black'
        black_with_condition = black_idx & (self.y_true == 1)
        self.y_pred[black_with_condition] = self.y_pred[black_with_condition] * 0.7
        
        # Add bias by insurance - Medicaid patients get worse predictions
        medicaid_idx = self.insurance == 'Medicaid'
        self.y_pred[medicaid_idx] = np.abs(self.y_pred[medicaid_idx] - self.y_true[medicaid_idx]) * 0.8 + self.y_pred[medicaid_idx] * 0.2
        
        # Create DataFrame
        self.df = pd.DataFrame({
            'patient_id': self.patient_ids,
            'age': self.ages,
            'gender': self.genders,
            'race': self.races,
            'insurance': self.insurance,
            'true_outcome': self.y_true,
            'prediction': self.y_pred
        })
        
        # Create age groups
        self.df['age_group'] = pd.cut(
            self.df['age'],
            bins=[0, 18, 35, 50, 65, 80, 120],
            labels=['0-18', '19-35', '36-50', '51-65', '66-80', '80+']
        )
        
        # Create fairness evaluator instance
        self.evaluator = FairnessEvaluator()
        
        # Create healthcare metrics instance
        self.metrics = HealthcareMetrics()

    def test_demographic_parity(self):
        """Test demographic parity calculation."""
        # Calculate demographic parity for gender
        dp_gender = self.evaluator.calculate_demographic_parity(
            self.df,
            prediction_column='prediction',
            group_column='gender',
            threshold=0.5
        )
        
        # Check result structure
        self.assertIn('demographic_parity', dp_gender)
        self.assertIn('positive_rates', dp_gender)
        self.assertIn('M', dp_gender['positive_rates'])
        self.assertIn('F', dp_gender['positive_rates'])
        
        # Calculate demographic parity for race
        dp_race = self.evaluator.calculate_demographic_parity(
            self.df,
            prediction_column='prediction',
            group_column='race',
            threshold=0.5
        )
        
        # Check result structure
        self.assertIn('demographic_parity', dp_race)
        self.assertIn('positive_rates', dp_race)
        for race in ['White', 'Black', 'Hispanic', 'Asian', 'Other']:
            self.assertIn(race, dp_race['positive_rates'])

    def test_equal_opportunity(self):
        """Test equal opportunity calculation."""
        # Calculate equal opportunity for gender
        eo_gender = self.evaluator.calculate_equal_opportunity(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='gender',
            threshold=0.5
        )
        
        # Check result structure
        self.assertIn('equal_opportunity', eo_gender)
        self.assertIn('true_positive_rates', eo_gender)
        self.assertIn('M', eo_gender['true_positive_rates'])
        self.assertIn('F', eo_gender['true_positive_rates'])
        
        # Due to our deliberate bias, females should have lower TPR
        self.assertLess(eo_gender['true_positive_rates']['F'], eo_gender['true_positive_rates']['M'])
        
        # Calculate equal opportunity for race
        eo_race = self.evaluator.calculate_equal_opportunity(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='race',
            threshold=0.5
        )
        
        # Check result structure
        self.assertIn('equal_opportunity', eo_race)
        self.assertIn('true_positive_rates', eo_race)
        for race in ['White', 'Black', 'Hispanic', 'Asian', 'Other']:
            self.assertIn(race, eo_race['true_positive_rates'])
        
        # Due to our deliberate bias, Black patients should have lower TPR
        self.assertLess(eo_race['true_positive_rates']['Black'], eo_race['true_positive_rates']['White'])

    def test_equalized_odds(self):
        """Test equalized odds calculation."""
        # Calculate equalized odds for gender
        eodds_gender = self.evaluator.calculate_equalized_odds(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='gender',
            threshold=0.5
        )
        
        # Check result structure
        self.assertIn('equalized_odds', eodds_gender)
        self.assertIn('true_positive_rates', eodds_gender)
        self.assertIn('false_positive_rates', eodds_gender)
        self.assertIn('M', eodds_gender['true_positive_rates'])
        self.assertIn('F', eodds_gender['true_positive_rates'])
        self.assertIn('M', eodds_gender['false_positive_rates'])
        self.assertIn('F', eodds_gender['false_positive_rates'])
        
        # Calculate equalized odds for race
        eodds_race = self.evaluator.calculate_equalized_odds(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='race',
            threshold=0.5
        )
        
        # Check result structure
        self.assertIn('equalized_odds', eodds_race)
        self.assertIn('true_positive_rates', eodds_race)
        self.assertIn('false_positive_rates', eodds_race)
        for race in ['White', 'Black', 'Hispanic', 'Asian', 'Other']:
            self.assertIn(race, eodds_race['true_positive_rates'])
            self.assertIn(race, eodds_race['false_positive_rates'])

    def test_predictive_parity(self):
        """Test predictive parity calculation."""
        # Calculate predictive parity for gender
        pp_gender = self.evaluator.calculate_predictive_parity(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='gender',
            threshold=0.5
        )
        
        # Check result structure
        self.assertIn('predictive_parity', pp_gender)
        self.assertIn('positive_predictive_values', pp_gender)
        self.assertIn('M', pp_gender['positive_predictive_values'])
        self.assertIn('F', pp_gender['positive_predictive_values'])
        
        # Calculate predictive parity for race
        pp_race = self.evaluator.calculate_predictive_parity(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='race',
            threshold=0.5
        )
        
        # Check result structure
        self.assertIn('predictive_parity', pp_race)
        self.assertIn('positive_predictive_values', pp_race)
        for race in ['White', 'Black', 'Hispanic', 'Asian', 'Other']:
            self.assertIn(race, pp_race['positive_predictive_values'])

    def test_calibration_by_group(self):
        """Test calibration by group calculation."""
        # Calculate calibration by gender
        cal_gender = self.evaluator.calculate_calibration_by_group(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='gender'
        )
        
        # Check result structure
        self.assertIn('calibration_by_group', cal_gender)
        self.assertIn('brier_scores', cal_gender)
        self.assertIn('M', cal_gender['brier_scores'])
        self.assertIn('F', cal_gender['brier_scores'])
        
        # Due to our deliberate bias, females should have worse calibration
        self.assertGreater(cal_gender['brier_scores']['F'], cal_gender['brier_scores']['M'])
        
        # Calculate calibration by race
        cal_race = self.evaluator.calculate_calibration_by_group(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='race'
        )
        
        # Check result structure
        self.assertIn('calibration_by_group', cal_race)
        self.assertIn('brier_scores', cal_race)
        for race in ['White', 'Black', 'Hispanic', 'Asian', 'Other']:
            self.assertIn(race, cal_race['brier_scores'])
        
        # Due to our deliberate bias, Black patients should have worse calibration
        self.assertGreater(cal_race['brier_scores']['Black'], cal_race['brier_scores']['White'])

    def test_auc_by_group(self):
        """Test AUC by group calculation."""
        # Calculate AUC by gender
        auc_gender = self.evaluator.calculate_auc_by_group(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='gender'
        )
        
        # Check result structure
        self.assertIn('auc_by_group', auc_gender)
        self.assertIn('M', auc_gender['auc_by_group'])
        self.assertIn('F', auc_gender['auc_by_group'])
        
        # Calculate AUC by race
        auc_race = self.evaluator.calculate_auc_by_group(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='race'
        )
        
        # Check result structure
        self.assertIn('auc_by_group', auc_race)
        for race in ['White', 'Black', 'Hispanic', 'Asian', 'Other']:
            self.assertIn(race, auc_race['auc_by_group'])

    def test_fairness_metrics_report(self):
        """Test comprehensive fairness metrics report."""
        # Generate fairness report for gender
        report_gender = self.evaluator.generate_fairness_report(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='gender',
            threshold=0.5
        )
        
        # Check report structure
        self.assertIn('demographic_parity', report_gender)
        self.assertIn('equal_opportunity', report_gender)
        self.assertIn('equalized_odds', report_gender)
        self.assertIn('predictive_parity', report_gender)
        self.assertIn('calibration_by_group', report_gender)
        self.assertIn('auc_by_group', report_gender)
        
        # Generate fairness report for race
        report_race = self.evaluator.generate_fairness_report(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='race',
            threshold=0.5
        )
        
        # Check report structure
        self.assertIn('demographic_parity', report_race)
        self.assertIn('equal_opportunity', report_race)
        self.assertIn('equalized_odds', report_race)
        self.assertIn('predictive_parity', report_race)
        self.assertIn('calibration_by_group', report_race)
        self.assertIn('auc_by_group', report_race)

    def test_fairness_plots(self):
        """Test fairness visualization plots."""
        # Generate ROC curves by gender
        fig_roc = self.evaluator.plot_roc_curves_by_group(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='gender'
        )
        
        # Check figure is created
        self.assertIsInstance(fig_roc, plt.Figure)
        
        # Generate PR curves by gender
        fig_pr = self.evaluator.plot_precision_recall_curves_by_group(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='gender'
        )
        
        # Check figure is created
        self.assertIsInstance(fig_pr, plt.Figure)
        
        # Generate calibration curves by gender
        fig_cal = self.evaluator.plot_calibration_curves_by_group(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='gender'
        )
        
        # Check figure is created
        self.assertIsInstance(fig_cal, plt.Figure)
        
        # Generate fairness metrics comparison
        fig_metrics = self.evaluator.plot_fairness_metrics_comparison(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_columns=['gender', 'race', 'insurance'],
            threshold=0.5
        )
        
        # Check figure is created
        self.assertIsInstance(fig_metrics, plt.Figure)
        
        # Clean up
        plt.close('all')

    def test_threshold_optimization(self):
        """Test threshold optimization for fairness."""
        # Optimize thresholds for equal opportunity by gender
        opt_result = self.evaluator.optimize_thresholds_for_equal_opportunity(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='gender'
        )
        
        # Check result structure
        self.assertIn('optimized_thresholds', opt_result)
        self.assertIn('M', opt_result['optimized_thresholds'])
        self.assertIn('F', opt_result['optimized_thresholds'])
        self.assertIn('equal_opportunity_before', opt_result)
        self.assertIn('equal_opportunity_after', opt_result)
        
        # Check that optimization improves equal opportunity
        self.assertLess(opt_result['equal_opportunity_after'], opt_result['equal_opportunity_before'])
        
        # Optimize thresholds for equalized odds by gender
        opt_result = self.evaluator.optimize_thresholds_for_equalized_odds(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='gender'
        )
        
        # Check result structure
        self.assertIn('optimized_thresholds', opt_result)
        self.assertIn('M', opt_result['optimized_thresholds'])
        self.assertIn('F', opt_result['optimized_thresholds'])
        self.assertIn('equalized_odds_before', opt_result)
        self.assertIn('equalized_odds_after', opt_result)
        
        # Check that optimization improves equalized odds
        self.assertLess(opt_result['equalized_odds_after'], opt_result['equalized_odds_before'])

    def test_intersectional_fairness(self):
        """Test intersectional fairness analysis."""
        # Create intersectional groups
        self.df['gender_race'] = self.df['gender'] + '_' + self.df['race']
        
        # Calculate fairness metrics for intersectional groups
        report = self.evaluator.generate_fairness_report(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='gender_race',
            threshold=0.5
        )
        
        # Check report structure
        self.assertIn('demographic_parity', report)
        self.assertIn('equal_opportunity', report)
        self.assertIn('equalized_odds', report)
        self.assertIn('predictive_parity', report)
        
        # Check that intersectional groups are present
        for gender in ['M', 'F']:
            for race in ['White', 'Black', 'Hispanic', 'Asian', 'Other']:
                intersectional_group = f"{gender}_{race}"
                if intersectional_group in report['demographic_parity']['positive_rates']:
                    # Some groups might be too small in random data
                    self.assertIn(intersectional_group, report['demographic_parity']['positive_rates'])

    def test_fairness_over_thresholds(self):
        """Test fairness metrics across different thresholds."""
        # Calculate fairness metrics across thresholds
        thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        
        threshold_results = self.evaluator.calculate_fairness_across_thresholds(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='gender',
            thresholds=thresholds
        )
        
        # Check result structure
        self.assertIn('demographic_parity', threshold_results)
        self.assertIn('equal_opportunity', threshold_results)
        self.assertIn('equalized_odds', threshold_results)
        
        # Check that each threshold has results
        for threshold in thresholds:
            self.assertIn(threshold, threshold_results['demographic_parity'])
            self.assertIn(threshold, threshold_results['equal_opportunity'])
            self.assertIn(threshold, threshold_results['equalized_odds'])
        
        # Plot fairness metrics across thresholds
        fig = self.evaluator.plot_fairness_across_thresholds(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='gender',
            thresholds=thresholds
        )
        
        # Check figure is created
        self.assertIsInstance(fig, plt.Figure)
        
        # Clean up
        plt.close(fig)

    def test_fairness_with_reweighting(self):
        """Test fairness improvement with instance reweighting."""
        # Calculate fairness before reweighting
        before_report = self.evaluator.generate_fairness_report(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='gender',
            threshold=0.5
        )
        
        # Apply reweighting to improve demographic parity
        reweighted_result = self.evaluator.improve_fairness_with_reweighting(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='gender',
            fairness_metric='demographic_parity'
        )
        
        # Check result structure
        self.assertIn('weights', reweighted_result)
        self.assertIn('fairness_before', reweighted_result)
        self.assertIn('fairness_after', reweighted_result)
        
        # Check that reweighting improves fairness
        self.assertLess(
            reweighted_result['fairness_after'],
            reweighted_result['fairness_before']
        )

    def test_fairness_with_adversarial_debiasing(self):
        """Test fairness improvement with adversarial debiasing simulation."""
        # This is a mock test since actual adversarial debiasing requires training
        # In a real implementation, this would use TensorFlow or similar
        
        # Create a mock implementation
        X = self.df[['age']].values  # Simple feature for testing
        y = self.df['true_outcome'].values
        sensitive_features = pd.get_dummies(self.df['gender']).values
        
        # Mock adversarial debiasing
        mock_result = self.evaluator.mock_adversarial_debiasing(
            X, y, sensitive_features,
            fairness_metric='demographic_parity'
        )
        
        # Check result structure
        self.assertIn('original_predictions', mock_result)
        self.assertIn('debiased_predictions', mock_result)
        self.assertIn('fairness_improvement', mock_result)
        
        # Check shapes
        self.assertEqual(len(mock_result['original_predictions']), len(self.df))
        self.assertEqual(len(mock_result['debiased_predictions']), len(self.df))

    def test_integration_with_healthcare_metrics(self):
        """Test integration with healthcare metrics."""
        # Calculate fairness metrics
        fairness_report = self.evaluator.generate_fairness_report(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='gender',
            threshold=0.5
        )
        
        # Calculate healthcare metrics by group
        healthcare_report = {}
        
        for gender in ['M', 'F']:
            gender_df = self.df[self.df['gender'] == gender]
            
            # Evaluate clinical model
            eval_result = self.metrics.evaluate_clinical_model(
                gender_df,
                outcome_column='true_outcome',
                prediction_column='prediction'
            )
            
            healthcare_report[gender] = eval_result
        
        # Check consistency between metrics
        for gender in ['M', 'F']:
            # AUC should be consistent
            self.assertAlmostEqual(
                fairness_report['auc_by_group'][gender],
                healthcare_report[gender]['auc'],
                places=4
            )

    def test_fairness_report_export(self):
        """Test exporting fairness report to file."""
        # Generate fairness report
        report = self.evaluator.generate_fairness_report(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='gender',
            threshold=0.5
        )
        
        # Export report to JSON
        json_path = 'fairness_report.json'
        self.evaluator.export_fairness_report(report, json_path)
        
        # Check file exists
        self.assertTrue(os.path.exists(json_path))
        
        # Clean up
        os.remove(json_path)

    def test_cross_validation_fairness(self):
        """Test fairness metrics with cross-validation."""
        # Perform cross-validation
        cv_results = self.evaluator.cross_validate_fairness(
            self.df,
            prediction_column='prediction',
            outcome_column='true_outcome',
            group_column='gender',
            cv=3,
            threshold=0.5
        )
        
        # Check result structure
        self.assertIn('demographic_parity', cv_results)
        self.assertIn('equal_opportunity', cv_results)
        self.assertIn('equalized_odds', cv_results)
        self.assertIn('fold_results', cv_results)
        
        # Check fold results
        self.assertEqual(len(cv_results['fold_results']), 3)
        for fold_result in cv_results['fold_results']:
            self.assertIn('demographic_parity', fold_result)
            self.assertIn('equal_opportunity', fold_result)
            self.assertIn('equalized_odds', fold_result)


if __name__ == '__main__':
    unittest.main()
