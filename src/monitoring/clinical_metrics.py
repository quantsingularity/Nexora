class ClinicalMetrics:
    @staticmethod
    def preventability_score(y_true, y_pred, adverse_events):
        """Calculates preventability score (PSS-30)"""
        tp = np.sum((y_pred == 1) & (y_true == 1) & (adverse_events == 1))
        fp = np.sum((y_pred == 1) & (y_true == 0))
        return tp / (tp + fp + 1e-7)

    @staticmethod
    def comorbidity_index(diagnoses):
        """Charlson Comorbidity Index calculation"""
        cci_weights = {
            "MI": 1,
            "CHF": 1,
            "PVD": 1,
            "CVA": 1,
            "DEMENTIA": 1,
            "COPD": 1,
            "DIABETES": 1,
        }
        return sum(cci_weights.get(dx, 0) for dx in diagnoses)

    @staticmethod
    def medication_risk_score(medications):
        """Calculate anticholinergic burden score"""
        acb_scale = {"amitriptyline": 3, "diphenhydramine": 3, "paroxetine": 2}
        return sum(acb_scale.get(med, 0) for med in medications)
