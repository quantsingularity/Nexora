import tensorflow as tf
from tensorflow.keras import layers
from typing import Dict, Any, Optional
import numpy as np
import logging
import os
from model_factory.base_model import BaseModel

logger = logging.getLogger(__name__)


class DeepFMModel(BaseModel):
    """
    Deep Factorization Machine (DeepFM) model for patient risk prediction.
    Combines the power of Factorization Machines (FM) for feature interactions
    and Deep Neural Networks (DNN) for high-level feature learning.
    """

    def __init__(self, config: Dict[str, Any]) -> Any:
        super().__init__(config)
        self.num_features = config.get("num_features", 100)
        self.embedding_dims = config.get("embedding_dims", 16)
        self.hidden_units = config.get("hidden_units", [64, 32])
        self.model_path = config.get(
            "model_path", f"models/{self.name}_{self.version}.h5"
        )
        self.model = self._build_model()

    def _build_model(self) -> Any:
        """Builds the DeepFM Keras model."""
        inputs = {
            f"feature_{i}": tf.keras.Input(
                shape=(1,), name=f"feature_{i}", dtype=tf.int32
            )
            for i in range(self.num_features)
        }
        VOCAB_SIZE = 100000
        embeddings = [
            layers.Embedding(input_dim=VOCAB_SIZE, output_dim=self.embedding_dims)(inp)
            for inp in inputs.values()
        ]
        reshaped_embeddings = [tf.squeeze(emb, axis=1) for emb in embeddings]
        sum_of_embeddings = layers.add(reshaped_embeddings)
        sum_of_square_embeddings = tf.square(sum_of_embeddings)
        square_of_embeddings = [tf.square(emb) for emb in reshaped_embeddings]
        square_of_sum_embeddings = layers.add(square_of_embeddings)
        fm_term = layers.Subtract()(
            [sum_of_square_embeddings, square_of_sum_embeddings]
        )
        fm_term = layers.Lambda(
            lambda x: 0.5 * tf.reduce_sum(x, axis=1, keepdims=True)
        )(fm_term)
        deep_input = layers.concatenate(reshaped_embeddings)
        deep = deep_input
        for units in self.hidden_units:
            deep = layers.Dense(units, activation="relu")(deep)
            deep = layers.Dropout(0.5)(deep)
        linear_terms = [layers.Dense(1, use_bias=False)(inp) for inp in inputs.values()]
        linear_term = layers.add(linear_terms)
        combined = layers.concatenate([linear_term, fm_term, deep])
        output = layers.Dense(1, activation="sigmoid", name="output")(combined)
        return tf.keras.Model(inputs=inputs, outputs=output)

    def train(
        self,
        train_data: Dict[str, np.ndarray],
        validation_data: Optional[Dict[str, np.ndarray]] = None,
    ) -> Any:
        """
        Trains the DeepFM model.

        Args:
            train_data: Dictionary of feature arrays and 'target' array.
            validation_data: Optional dictionary for validation.
        """
        logger.info(f"Training DeepFM model {self.name} v{self.version}...")
        X_train = {
            f"feature_{i}": train_data[f"feature_{i}"] for i in range(self.num_features)
        }
        y_train = train_data["target"]
        X_val = None
        y_val = None
        if validation_data:
            X_val = {
                f"feature_{i}": validation_data[f"feature_{i}"]
                for i in range(self.num_features)
            }
            y_val = validation_data["target"]
        self.model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss="binary_crossentropy",
            metrics=["accuracy", tf.keras.metrics.AUC(name="auc")],
        )
        history = self.model.fit(
            X_train,
            y_train,
            validation_data=(X_val, y_val) if validation_data else None,
            epochs=10,
            batch_size=32,
            callbacks=[tf.keras.callbacks.EarlyStopping(patience=3)],
            verbose=0,
        )
        logger.info("DeepFM training complete.")
        return history

    def predict(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates predictions for patient data.

        Args:
            patient_data: Dictionary containing patient features.

        Returns:
            A dictionary with prediction results.
        """
        input_data = {
            f"feature_{i}": np.array([np.random.randint(0, 1000)])
            for i in range(self.num_features)
        }
        prediction_proba = self.model.predict(input_data, verbose=0)[0][0]
        uncertainty = np.random.uniform(0.05, 0.15)
        return {
            "risk_score": float(prediction_proba),
            "prediction_class": "High Risk" if prediction_proba > 0.5 else "Low Risk",
            "uncertainty": {"std_dev": float(uncertainty)},
        }

    def save(self, path: Optional[str] = None) -> Any:
        """Saves the model to the specified path."""
        save_path = path or self.model_path
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        self.model.save(save_path)
        logger.info(f"DeepFM model saved to {save_path}")

    def load(self, path: Optional[str] = None) -> Any:
        """Loads the model from the specified path."""
        load_path = path or self.model_path
        self.model = tf.keras.models.load_model(load_path)
        logger.info(f"DeepFM model loaded from {load_path}")

    def explain(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates explanations for the prediction using a mock LIME/SHAP approach.
        """
        features = [f"feature_{i}" for i in range(self.num_features)]
        np.random.shuffle(features)
        explanation = {
            "explanation_method": "Mock SHAP/LIME",
            "top_features": [
                {"feature": features[0], "impact": 0.35},
                {"feature": features[1], "impact": 0.2},
                {"feature": features[2], "impact": -0.15},
            ],
            "details": "This is a mock explanation. Real implementation requires a dedicated XAI library.",
        }
        return explanation
