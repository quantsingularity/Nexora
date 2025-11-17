"""
Transformer Model Module for Nexora

This module implements transformer-based deep learning models for clinical prediction tasks,
including time series forecasting, sequence classification, and multimodal fusion of
clinical data. It provides utilities for preprocessing clinical data into formats
suitable for transformer architectures and implements custom attention mechanisms
optimized for sparse and irregular clinical time series.
"""

import json
import logging
import math
import os
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import tensorflow as tf
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from tensorflow import keras
from tensorflow.keras import layers

logger = logging.getLogger(__name__)


class PositionalEncoding(nn.Module):
    """
    Positional encoding for transformer models.

    This class implements sinusoidal positional encodings as described in
    "Attention Is All You Need" (Vaswani et al., 2017).
    """

    def __init__(self, d_model: int, max_seq_length: int = 5000, dropout: float = 0.1):
        """
        Initialize positional encoding.

        Args:
            d_model: Dimensionality of the model
            max_seq_length: Maximum sequence length
            dropout: Dropout rate
        """
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        # Create positional encoding matrix
        pe = torch.zeros(max_seq_length, d_model)
        position = torch.arange(0, max_seq_length, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)

        # Register buffer (persistent state)
        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Add positional encoding to input tensor.

        Args:
            x: Input tensor of shape [batch_size, seq_length, d_model]

        Returns:
            Tensor with positional encoding added
        """
        x = x + self.pe[:, : x.size(1), :]
        return self.dropout(x)


class TimeAwareMultiHeadAttention(nn.Module):
    """
    Time-aware multi-head attention for clinical time series.

    This class extends standard multi-head attention with time-aware
    mechanisms to handle irregular sampling and temporal patterns in
    clinical data.
    """

    def __init__(
        self,
        d_model: int,
        num_heads: int,
        dropout: float = 0.1,
        use_time_decay: bool = True,
    ):
        """
        Initialize time-aware multi-head attention.

        Args:
            d_model: Dimensionality of the model
            num_heads: Number of attention heads
            dropout: Dropout rate
            use_time_decay: Whether to use time decay in attention weights
        """
        super().__init__()

        assert d_model % num_heads == 0, "d_model must be divisible by num_heads"

        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        self.use_time_decay = use_time_decay

        # Linear projections
        self.query = nn.Linear(d_model, d_model)
        self.key = nn.Linear(d_model, d_model)
        self.value = nn.Linear(d_model, d_model)
        self.time_proj = nn.Linear(1, self.d_k) if use_time_decay else None

        # Output projection
        self.output = nn.Linear(d_model, d_model)

        # Dropout
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        time_diffs: Optional[torch.Tensor] = None,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Forward pass for time-aware multi-head attention.

        Args:
            query: Query tensor of shape [batch_size, seq_length, d_model]
            key: Key tensor of shape [batch_size, seq_length, d_model]
            value: Value tensor of shape [batch_size, seq_length, d_model]
            time_diffs: Time differences tensor of shape [batch_size, seq_length, seq_length]
            mask: Attention mask tensor

        Returns:
            Output tensor after attention
        """
        batch_size = query.size(0)

        # Linear projections and reshape for multi-head attention
        q = (
            self.query(query)
            .view(batch_size, -1, self.num_heads, self.d_k)
            .transpose(1, 2)
        )
        k = self.key(key).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        v = (
            self.value(value)
            .view(batch_size, -1, self.num_heads, self.d_k)
            .transpose(1, 2)
        )

        # Calculate attention scores
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.d_k)

        # Apply time decay if enabled and time differences are provided
        if self.use_time_decay and time_diffs is not None:
            # Project time differences to attention space
            time_diffs = time_diffs.unsqueeze(
                -1
            )  # [batch_size, seq_length, seq_length, 1]
            time_features = self.time_proj(
                time_diffs
            )  # [batch_size, seq_length, seq_length, d_k]

            # Reshape for multi-head attention
            time_features = time_features.unsqueeze(1).expand(
                -1, self.num_heads, -1, -1, -1
            )

            # Apply time decay to attention scores
            time_decay = torch.sum(
                time_features, dim=-1
            )  # [batch_size, num_heads, seq_length, seq_length]
            scores = scores - time_decay

        # Apply mask if provided
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)

        # Apply softmax and dropout
        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)

        # Apply attention weights to values
        output = torch.matmul(attn_weights, v)

        # Reshape and apply output projection
        output = output.transpose(1, 2).contiguous().view(batch_size, -1, self.d_model)
        output = self.output(output)

        return output


class ClinicalTransformerEncoder(nn.Module):
    """
    Transformer encoder adapted for clinical time series data.

    This class implements a transformer encoder with time-aware attention
    mechanisms and additional features for handling clinical data.
    """

    def __init__(
        self,
        d_model: int,
        num_heads: int,
        d_ff: int,
        dropout: float = 0.1,
        use_time_decay: bool = True,
    ):
        """
        Initialize clinical transformer encoder.

        Args:
            d_model: Dimensionality of the model
            num_heads: Number of attention heads
            d_ff: Dimensionality of feed-forward network
            dropout: Dropout rate
            use_time_decay: Whether to use time decay in attention
        """
        super().__init__()

        # Time-aware multi-head attention
        self.attention = TimeAwareMultiHeadAttention(
            d_model=d_model,
            num_heads=num_heads,
            dropout=dropout,
            use_time_decay=use_time_decay,
        )

        # Feed-forward network
        self.feed_forward = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
        )

        # Layer normalization
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)

        # Dropout
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        x: torch.Tensor,
        time_diffs: Optional[torch.Tensor] = None,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Forward pass for clinical transformer encoder.

        Args:
            x: Input tensor of shape [batch_size, seq_length, d_model]
            time_diffs: Time differences tensor
            mask: Attention mask tensor

        Returns:
            Output tensor after transformer encoder
        """
        # Multi-head attention with residual connection and layer normalization
        attn_output = self.attention(
            query=x, key=x, value=x, time_diffs=time_diffs, mask=mask
        )
        x = self.norm1(x + self.dropout(attn_output))

        # Feed-forward network with residual connection and layer normalization
        ff_output = self.feed_forward(x)
        x = self.norm2(x + self.dropout(ff_output))

        return x


class ClinicalTransformerModel(nn.Module):
    """
    Transformer model for clinical prediction tasks.

    This class implements a complete transformer model for clinical prediction
    tasks, including classification and regression.
    """

    def __init__(
        self,
        input_dim: int,
        d_model: int = 128,
        num_heads: int = 8,
        num_encoder_layers: int = 6,
        d_ff: int = 512,
        dropout: float = 0.1,
        max_seq_length: int = 1000,
        use_time_features: bool = True,
        num_classes: Optional[int] = None,
        task_type: str = "classification",
    ):
        """
        Initialize clinical transformer model.

        Args:
            input_dim: Dimensionality of input features
            d_model: Dimensionality of the model
            num_heads: Number of attention heads
            num_encoder_layers: Number of encoder layers
            d_ff: Dimensionality of feed-forward network
            dropout: Dropout rate
            max_seq_length: Maximum sequence length
            use_time_features: Whether to use time features
            num_classes: Number of output classes (for classification)
            task_type: Type of task ('classification' or 'regression')
        """
        super().__init__()

        self.input_dim = input_dim
        self.d_model = d_model
        self.use_time_features = use_time_features
        self.task_type = task_type

        # Input embedding
        self.embedding = nn.Linear(input_dim, d_model)

        # Positional encoding
        self.positional_encoding = PositionalEncoding(
            d_model=d_model, max_seq_length=max_seq_length, dropout=dropout
        )

        # Encoder layers
        self.encoder_layers = nn.ModuleList(
            [
                ClinicalTransformerEncoder(
                    d_model=d_model,
                    num_heads=num_heads,
                    d_ff=d_ff,
                    dropout=dropout,
                    use_time_decay=use_time_features,
                )
                for _ in range(num_encoder_layers)
            ]
        )

        # Output layer
        if task_type == "classification":
            assert (
                num_classes is not None
            ), "num_classes must be specified for classification"
            self.output_layer = nn.Linear(d_model, num_classes)
        elif task_type == "regression":
            self.output_layer = nn.Linear(d_model, 1)
        else:
            raise ValueError(f"Unsupported task type: {task_type}")

    def forward(
        self,
        x: torch.Tensor,
        time_values: Optional[torch.Tensor] = None,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Forward pass for clinical transformer model.

        Args:
            x: Input tensor of shape [batch_size, seq_length, input_dim]
            time_values: Time values tensor of shape [batch_size, seq_length]
            mask: Attention mask tensor

        Returns:
            Output tensor for the prediction task
        """
        # Calculate time differences if time values are provided
        time_diffs = None
        if self.use_time_features and time_values is not None:
            # Calculate pairwise time differences
            time_values = time_values.unsqueeze(-1)  # [batch_size, seq_length, 1]
            time_diffs = torch.abs(
                time_values - time_values.transpose(-2, -1)
            )  # [batch_size, seq_length, seq_length]

        # Input embedding
        x = self.embedding(x)

        # Add positional encoding
        x = self.positional_encoding(x)

        # Apply encoder layers
        for encoder_layer in self.encoder_layers:
            x = encoder_layer(x, time_diffs=time_diffs, mask=mask)

        # Global pooling (mean of sequence)
        if mask is not None:
            # Apply mask for proper averaging
            mask_expanded = mask.unsqueeze(-1).expand_as(x)
            x = (x * mask_expanded).sum(dim=1) / mask_expanded.sum(dim=1)
        else:
            x = x.mean(dim=1)

        # Output layer
        x = self.output_layer(x)

        # Apply activation for classification
        if self.task_type == "classification":
            x = F.log_softmax(x, dim=-1)

        return x


class ClinicalTransformerPreprocessor:
    """
    Preprocessor for clinical data to be used with transformer models.

    This class handles preprocessing of clinical time series data into
    formats suitable for transformer models, including handling of
    irregular sampling, missing values, and feature normalization.
    """

    def __init__(
        self,
        time_column: str = "timestamp",
        patient_id_column: str = "patient_id",
        feature_columns: Optional[List[str]] = None,
        max_seq_length: int = 1000,
        padding_value: float = 0.0,
        normalization: str = "standard",
        handle_missing: str = "forward_fill",
    ):
        """
        Initialize clinical transformer preprocessor.

        Args:
            time_column: Column name for timestamps
            patient_id_column: Column name for patient IDs
            feature_columns: List of feature column names
            max_seq_length: Maximum sequence length
            padding_value: Value to use for padding
            normalization: Type of normalization ('standard', 'minmax', or None)
            handle_missing: Strategy for handling missing values
        """
        self.time_column = time_column
        self.patient_id_column = patient_id_column
        self.feature_columns = feature_columns
        self.max_seq_length = max_seq_length
        self.padding_value = padding_value
        self.normalization = normalization
        self.handle_missing = handle_missing

        # Initialize scalers
        if normalization == "standard":
            self.scaler = StandardScaler()
        elif normalization == "minmax":
            self.scaler = MinMaxScaler()
        elif normalization is None:
            self.scaler = None
        else:
            raise ValueError(f"Unsupported normalization: {normalization}")

        logger.info(
            f"Initialized ClinicalTransformerPreprocessor with {normalization} normalization"
        )

    def fit(self, df: pd.DataFrame) -> "ClinicalTransformerPreprocessor":
        """
        Fit the preprocessor to the data.

        Args:
            df: Input DataFrame

        Returns:
            Fitted preprocessor instance
        """
        # Validate required columns
        if self.time_column not in df.columns:
            raise ValueError(
                f"Time column '{self.time_column}' not found in input data"
            )

        if self.patient_id_column not in df.columns:
            raise ValueError(
                f"Patient ID column '{self.patient_id_column}' not found in input data"
            )

        # Determine feature columns if not provided
        if self.feature_columns is None:
            self.feature_columns = [
                col
                for col in df.columns
                if col not in [self.time_column, self.patient_id_column]
            ]
            logger.info(
                f"Automatically determined {len(self.feature_columns)} feature columns"
            )

        # Fit scaler if normalization is enabled
        if self.scaler is not None:
            # Flatten all feature values for fitting
            all_values = df[self.feature_columns].values.flatten().reshape(-1, 1)
            # Remove NaN values for fitting
            all_values = all_values[~np.isnan(all_values)]
            self.scaler.fit(all_values)
            logger.info(f"Fitted {self.normalization} scaler to feature values")

        return self

    def transform(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Transform the data into format suitable for transformer models.

        Args:
            df: Input DataFrame

        Returns:
            Tuple of (sequences, time_values, masks)
        """
        # Validate required columns
        if self.time_column not in df.columns:
            raise ValueError(
                f"Time column '{self.time_column}' not found in input data"
            )

        if self.patient_id_column not in df.columns:
            raise ValueError(
                f"Patient ID column '{self.patient_id_column}' not found in input data"
            )

        # Ensure timestamps are datetime
        if not pd.api.types.is_datetime64_any_dtype(df[self.time_column]):
            df[self.time_column] = pd.to_datetime(df[self.time_column])

        # Group by patient
        grouped = df.groupby(self.patient_id_column)

        # Initialize arrays
        num_patients = len(grouped)
        num_features = len(self.feature_columns)

        sequences = np.full(
            (num_patients, self.max_seq_length, num_features), self.padding_value
        )
        time_values = np.full((num_patients, self.max_seq_length), self.padding_value)
        masks = np.zeros((num_patients, self.max_seq_length))

        # Process each patient
        for i, (patient_id, patient_data) in enumerate(grouped):
            # Sort by timestamp
            patient_data = patient_data.sort_values(self.time_column)

            # Truncate if sequence is too long
            if len(patient_data) > self.max_seq_length:
                patient_data = patient_data.iloc[-self.max_seq_length :]

            # Get sequence length
            seq_length = len(patient_data)

            # Extract features
            features = patient_data[self.feature_columns].values

            # Handle missing values
            if self.handle_missing == "forward_fill":
                # Forward fill missing values
                for j in range(num_features):
                    feature_values = features[:, j]
                    mask = ~np.isnan(feature_values)
                    indices = np.arange(len(feature_values))
                    valid_indices = indices[mask]
                    if len(valid_indices) > 0:
                        valid_values = feature_values[mask]
                        # Get index of last valid value for each position
                        last_valid_idx = np.maximum.accumulate(
                            np.where(mask, indices, -1)
                        )
                        # Fill with last valid value where possible
                        mask_to_fill = (last_valid_idx != -1) & ~mask
                        if np.any(mask_to_fill):
                            feature_values[mask_to_fill] = valid_values[
                                last_valid_idx[mask_to_fill]
                            ]
                    features[:, j] = feature_values

            # Apply normalization if enabled
            if self.scaler is not None:
                # Reshape for scaler
                flat_features = features.reshape(-1, 1)
                # Remember NaN positions
                nan_mask = np.isnan(flat_features)
                # Replace NaNs with 0 for scaling
                flat_features[nan_mask] = 0
                # Scale features
                scaled_features = self.scaler.transform(flat_features)
                # Restore NaNs
                scaled_features[nan_mask] = np.nan
                # Reshape back
                features = scaled_features.reshape(seq_length, num_features)

            # Convert timestamps to relative time in days
            start_time = patient_data[self.time_column].min()
            timestamps = (
                patient_data[self.time_column] - start_time
            ).dt.total_seconds() / 86400  # days

            # Fill arrays
            sequences[i, :seq_length, :] = features
            time_values[i, :seq_length] = timestamps.values
            masks[i, :seq_length] = 1

        return sequences, time_values, masks

    def fit_transform(
        self, df: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Fit the preprocessor and transform the data.

        Args:
            df: Input DataFrame

        Returns:
            Tuple of (sequences, time_values, masks)
        """
        return self.fit(df).transform(df)

    def save(self, path: str):
        """
        Save the preprocessor to a file.

        Args:
            path: Path to save the preprocessor
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # Prepare data to save
        data = {
            "time_column": self.time_column,
            "patient_id_column": self.patient_id_column,
            "feature_columns": self.feature_columns,
            "max_seq_length": self.max_seq_length,
            "padding_value": self.padding_value,
            "normalization": self.normalization,
            "handle_missing": self.handle_missing,
        }

        # Save preprocessor configuration
        with open(path, "w") as f:
            json.dump(data, f)

        # Save scaler if available
        if self.scaler is not None:
            scaler_path = os.path.splitext(path)[0] + "_scaler.pkl"
            import joblib

            joblib.dump(self.scaler, scaler_path)

        logger.info(f"Saved preprocessor to {path}")

    @classmethod
    def load(cls, path: str) -> "ClinicalTransformerPreprocessor":
        """
        Load a preprocessor from a file.

        Args:
            path: Path to load the preprocessor from

        Returns:
            Loaded preprocessor instance
        """
        # Load preprocessor configuration
        with open(path, "r") as f:
            data = json.load(f)

        # Create preprocessor instance
        preprocessor = cls(
            time_column=data["time_column"],
            patient_id_column=data["patient_id_column"],
            feature_columns=data["feature_columns"],
            max_seq_length=data["max_seq_length"],
            padding_value=data["padding_value"],
            normalization=data["normalization"],
            handle_missing=data["handle_missing"],
        )

        # Load scaler if available
        scaler_path = os.path.splitext(path)[0] + "_scaler.pkl"
        if os.path.exists(scaler_path):
            import joblib

            preprocessor.scaler = joblib.load(scaler_path)

        logger.info(f"Loaded preprocessor from {path}")
        return preprocessor


def create_tensorflow_transformer_model(
    input_dim: int,
    d_model: int = 128,
    num_heads: int = 8,
    num_encoder_layers: int = 6,
    d_ff: int = 512,
    dropout: float = 0.1,
    max_seq_length: int = 1000,
    num_classes: Optional[int] = None,
    task_type: str = "classification",
) -> keras.Model:
    """
    Create a transformer model using TensorFlow/Keras.

    Args:
        input_dim: Dimensionality of input features
        d_model: Dimensionality of the model
        num_heads: Number of attention heads
        num_encoder_layers: Number of encoder layers
        d_ff: Dimensionality of feed-forward network
        dropout: Dropout rate
        max_seq_length: Maximum sequence length
        num_classes: Number of output classes (for classification)
        task_type: Type of task ('classification' or 'regression')

    Returns:
        Keras model
    """
    # Input layers
    inputs = keras.Input(shape=(None, input_dim))
    time_inputs = keras.Input(shape=(None,))
    mask_inputs = keras.Input(shape=(None,))

    # Expand mask for attention
    mask_expanded = tf.expand_dims(mask_inputs, axis=-1)

    # Input embedding
    x = layers.Dense(d_model)(inputs)

    # Positional encoding
    positions = tf.range(start=0, limit=tf.shape(x)[1], delta=1)
    positions = tf.cast(positions, tf.float32)
    pos_encoding = positional_encoding_tf(positions, d_model)
    x = x + pos_encoding

    # Apply mask
    x = x * mask_expanded

    # Transformer encoder layers
    for _ in range(num_encoder_layers):
        x = transformer_encoder_layer_tf(
            x, d_model, num_heads, d_ff, dropout, mask_inputs
        )

    # Global pooling with mask
    sum_mask = tf.reduce_sum(mask_inputs, axis=1, keepdims=True)
    x = tf.reduce_sum(x * mask_expanded, axis=1) / sum_mask

    # Output layer
    if task_type == "classification":
        assert (
            num_classes is not None
        ), "num_classes must be specified for classification"
        outputs = layers.Dense(num_classes, activation="softmax")(x)
    elif task_type == "regression":
        outputs = layers.Dense(1)(x)
    else:
        raise ValueError(f"Unsupported task type: {task_type}")

    # Create model
    model = keras.Model(inputs=[inputs, time_inputs, mask_inputs], outputs=outputs)

    # Compile model
    if task_type == "classification":
        model.compile(
            optimizer="adam",
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )
    else:
        model.compile(optimizer="adam", loss="mse", metrics=["mae"])

    return model


def positional_encoding_tf(positions, d_model):
    """
    Compute positional encoding for transformer models in TensorFlow.

    Args:
        positions: Position indices
        d_model: Dimensionality of the model

    Returns:
        Positional encoding tensor
    """
    angle_rates = 1 / np.power(
        10000, (2 * (tf.range(d_model, dtype=tf.float32) // 2)) / d_model
    )
    angle_rads = positions[:, tf.newaxis] * angle_rates[tf.newaxis, :]

    # Apply sin to even indices
    sines = tf.sin(angle_rads[:, 0::2])
    # Apply cos to odd indices
    cosines = tf.cos(angle_rads[:, 1::2])

    pos_encoding = tf.concat([sines, cosines], axis=-1)
    pos_encoding = pos_encoding[tf.newaxis, ...]

    return pos_encoding


def transformer_encoder_layer_tf(x, d_model, num_heads, d_ff, dropout, mask):
    """
    Transformer encoder layer implementation in TensorFlow.

    Args:
        x: Input tensor
        d_model: Dimensionality of the model
        num_heads: Number of attention heads
        d_ff: Dimensionality of feed-forward network
        dropout: Dropout rate
        mask: Attention mask tensor

    Returns:
        Output tensor after transformer encoder layer
    """
    # Multi-head attention
    attn_output = layers.MultiHeadAttention(
        num_heads=num_heads, key_dim=d_model // num_heads
    )(x, x, x, attention_mask=mask[:, tf.newaxis, tf.newaxis, :])

    # Dropout and residual connection
    attn_output = layers.Dropout(dropout)(attn_output)
    x = layers.LayerNormalization(epsilon=1e-6)(x + attn_output)

    # Feed-forward network
    ffn_output = layers.Dense(d_ff, activation="relu")(x)
    ffn_output = layers.Dense(d_model)(ffn_output)

    # Dropout and residual connection
    ffn_output = layers.Dropout(dropout)(ffn_output)
    x = layers.LayerNormalization(epsilon=1e-6)(x + ffn_output)

    return x
