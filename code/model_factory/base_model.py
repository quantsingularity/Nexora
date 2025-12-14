from typing import Dict, Any, Optional


class BaseModel:
    """
    Base class for all machine learning models in Nexora.
    Defines the required interface for training, prediction, and explanation.
    """

    def __init__(self, config: Dict[str, Any]) -> Any:
        self.config = config
        self.model = None
        self.name = config.get("name", "base_model")
        self.version = config.get("version", "1.0.0")

    def train(self, train_data: Any, validation_data: Optional[Any] = None) -> Any:
        """Trains the model."""
        raise NotImplementedError

    def predict(self, patient_data: Any) -> Dict[str, Any]:
        """Generates predictions for patient data."""
        raise NotImplementedError

    def explain(self, patient_data: Any) -> Dict[str, Any]:
        """Generates explanations for the prediction."""
        return {"explanation_method": "Not Implemented", "features": {}}

    def save(self, path: str) -> Any:
        """Saves the model and configuration."""
        raise NotImplementedError

    def load(self, path: str) -> Any:
        """Loads the model and configuration."""
        raise NotImplementedError
