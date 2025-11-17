class HealthcareFairness:
    def __init__(self, protected_attributes):
        self.metrics = {
            "demographic_parity": DemographicParity(),
            "equal_opportunity": EqualOpportunity(),
            "predictive_equality": PredictiveEquality(),
        }
        self.disparity_threshold = 0.1

    def evaluate(self, y_true, y_pred, sensitive_features):
        results = {}
        for name, metric in self.metrics.items():
            disparity = metric(y_true, y_pred, sensitive_features=sensitive_features)
            results[name] = {
                "value": disparity,
                "passed": disparity <= self.disparity_threshold,
            }

        if not all(r["passed"] for r in results.values()):
            raise ModelBiasError(f"Fairness thresholds violated: {results}")

        return results
