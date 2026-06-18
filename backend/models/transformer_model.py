"""
Transformer Temporal Delay Prediction Model
===========================================
Transformer encoder for sequential delay forecasting
Uses multi-head attention for temporal pattern learning
"""

from pathlib import Path
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("Warning: TensorFlow not available. Transformer model will be limited.")

from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .base_model import BaseModel


class TransformerBlock(layers.Layer):
    """Transformer encoder block with multi-head attention."""

    def __init__(self, embed_dim: int, num_heads: int, ff_dim: int, rate: float = 0.1):
        super().__init__()
        self.att = layers.MultiHeadAttention(num_heads=num_heads, key_dim=embed_dim // num_heads)
        self.ffn = keras.Sequential([
            layers.Dense(ff_dim, activation="relu"),
            layers.Dense(embed_dim),
        ])
        self.layernorm1 = layers.LayerNormalization(epsilon=1e-6)
        self.layernorm2 = layers.LayerNormalization(epsilon=1e-6)
        self.dropout1 = layers.Dropout(rate)
        self.dropout2 = layers.Dropout(rate)

    def call(self, inputs):
        attn_output = self.att(inputs, inputs)
        attn_output = self.dropout1(attn_output)
        out1 = self.layernorm1(inputs + attn_output)
        ffn_output = self.ffn(out1)
        ffn_output = self.dropout2(ffn_output)
        return self.layernorm2(out1 + ffn_output)


class TransformerModel(BaseModel):
    """Transformer model for temporal delay prediction."""

    def __init__(self, sequence_length: int = 24, model_dir: Optional[Path] = None):
        super().__init__("Transformer", model_dir)
        self.sequence_length = sequence_length
        self.scaler = StandardScaler()
        self.model = None
        self.history = None

    def create_sequences(self, data: np.ndarray, sequence_length: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for Transformer training.

        Args:
            data: 2D array of shape (samples, features)
            sequence_length: Number of timesteps per sequence

        Returns:
            (X, y) sequences
        """
        X, y = [], []
        for i in range(len(data) - sequence_length):
            X.append(data[i:i + sequence_length])
            y.append(data[i + sequence_length, -1])  # Last column is target
        return np.array(X), np.array(y)

    def _prepare_sequential_data(self, X: pd.DataFrame, y: pd.Series) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for Transformer training."""
        # Combine features and target
        data = X.copy()
        data['target'] = y.values

        # Scale features
        scaled = self.scaler.fit_transform(data)

        # Create sequences
        X_seq, y_seq = self.create_sequences(scaled, self.sequence_length)

        return X_seq, y_seq

    def build_model(self, input_shape: Tuple) -> keras.Model:
        """
        Build Transformer architecture.

        Args:
            input_shape: Shape of input sequences

        Returns:
            Compiled Keras model
        """
        inputs = keras.Input(shape=input_shape)
        x = inputs

        # Transformer blocks
        for _ in range(2):
            x = TransformerBlock(
                embed_dim=input_shape[1],
                num_heads=4,
                ff_dim=128,
                rate=0.1
            )(x)

        # Global pooling
        x = layers.GlobalAveragePooling1D()(x)

        # Output head
        x = layers.Dense(32, activation="relu")(x)
        x = layers.Dropout(0.1)(x)
        outputs = layers.Dense(1)(x)

        model = keras.Model(inputs=inputs, outputs=outputs)
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )

        return model

    def train(self, X_train: pd.DataFrame, y_train: pd.Series) -> Dict:
        """
        Train Transformer model.

        Args:
            X_train: Training features
            y_train: Training delays

        Returns:
            Training metrics dictionary
        """
        if not TENSORFLOW_AVAILABLE:
            print("Error: TensorFlow not installed. Install with: pip install tensorflow")
            return {}

        print(f"Training {self.model_name}...")

        self.feature_columns = X_train.columns.tolist()

        # Prepare sequential data
        print("  Preparing sequences...")
        try:
            X_seq, y_seq = self._prepare_sequential_data(X_train, y_train)

            if len(X_seq) < 100:
                print(f"  Warning: Only {len(X_seq)} sequences. Consider more data or shorter sequence length.")

            # Split for validation
            split_idx = int(0.8 * len(X_seq))
            X_train_seq = X_seq[:split_idx]
            y_train_seq = y_seq[:split_idx]
            X_val_seq = X_seq[split_idx:]
            y_val_seq = y_seq[split_idx:]

            # Build model
            print("  Building Transformer architecture...")
            self.model = self.build_model((X_seq.shape[1], X_seq.shape[2]))

            # Train
            print("  Training...")
            self.history = self.model.fit(
                X_train_seq, y_train_seq,
                validation_data=(X_val_seq, y_val_seq),
                epochs=50,
                batch_size=32,
                verbose=0
            )

            self.is_trained = True

            # Get training metrics
            y_pred_train = self.model.predict(X_train_seq, verbose=0)
            metrics = {
                "train_mae": float(mean_absolute_error(y_train_seq, y_pred_train)),
                "train_rmse": float(np.sqrt(mean_squared_error(y_train_seq, y_pred_train))),
                "train_r2": float(r2_score(y_train_seq, y_pred_train)),
            }

            self.metrics = metrics
            print(f"  MAE: {metrics['train_mae']:.3f} min")
            print(f"  RMSE: {metrics['train_rmse']:.3f} min")
            print(f"  R2: {metrics['train_r2']:.3f}")

            return metrics

        except Exception as e:
            print(f"  Error during training: {e}")
            return {}

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make delay predictions.

        Args:
            X: Features dataframe

        Returns:
            Predicted delays in minutes
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")

        try:
            # Prepare data
            data = X.copy()
            data['target'] = 0  # Placeholder for target

            # Scale
            scaled = self.scaler.transform(data)

            # Create sequences
            X_seq, _ = self.create_sequences(scaled, self.sequence_length)

            if len(X_seq) == 0:
                # Not enough data for sequences
                print("  Warning: Not enough data for Transformer sequences.")
                return np.full(len(X), self.metrics.get('train_mae', 1.0))

            # Predict
            predictions = self.model.predict(X_seq, verbose=0)
            return predictions.flatten()

        except Exception as e:
            print(f"  Error during prediction: {e}")
            return np.zeros(len(X))

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict:
        """
        Evaluate model on test set.

        Args:
            X_test: Test features
            y_test: Test delays

        Returns:
            Evaluation metrics
        """
        if len(X_test) <= self.sequence_length:
            print(f"{self.model_name} Evaluation:")
            print(f"  Insufficient test samples ({len(X_test)}) for Transformer evaluation (needs > {self.sequence_length})")
            return {
                "mae": float('nan'),
                "rmse": float('nan'),
                "r2": float('nan'),
                "samples": len(y_test),
                "note": "Insufficient samples"
            }

        try:
            y_pred = self.predict(X_test)
            metrics = {
                "mae": float(mean_absolute_error(y_test, y_pred)),
                "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
                "r2": float(r2_score(y_test, y_pred)),
                "samples": len(y_test),
            }

            print(f"\n{self.model_name} Evaluation:")
            print(f"  MAE: {metrics['mae']:.3f} min")
            print(f"  RMSE: {metrics['rmse']:.3f} min")
            print(f"  R2: {metrics['r2']:.3f}")

            return metrics
        except Exception as e:
            print(f"  Error during evaluation: {e}")
            return {
                "mae": float('nan'),
                "rmse": float('nan'),
                "r2": float('nan'),
                "error": str(e)
            }

    def save(self, filepath: Optional[Path] = None) -> str:
        """Save model to disk."""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")

        filepath = filepath or self.model_dir / "transformer_model"
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Save model
        self.model.save(str(filepath / "model.keras"))

        # Save metadata
        metadata = {
            "feature_columns": self.feature_columns,
            "sequence_length": self.sequence_length,
            "metrics": self.metrics,
        }

        import json
        with open(filepath / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"Model saved to {filepath}")
        return str(filepath)

    def load(self, filepath: Optional[Path] = None) -> bool:
        """Load model from disk."""
        filepath = filepath or self.model_dir / "transformer_model"
        filepath = Path(filepath)

        try:
            if not filepath.exists():
                print(f"Model file not found: {filepath}")
                return False

            # Load model with custom objects
            self.model = keras.models.load_model(
                str(filepath / "model.keras"),
                custom_objects={"TransformerBlock": TransformerBlock}
            )

            # Load metadata
            import json
            with open(filepath / "metadata.json", "r") as f:
                metadata = json.load(f)

            self.feature_columns = metadata["feature_columns"]
            self.sequence_length = metadata["sequence_length"]
            self.metrics = metadata["metrics"]
            self.is_trained = True

            print(f"Model loaded from {filepath}")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
