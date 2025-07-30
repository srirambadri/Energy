import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import SimpleRNN, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error
import numpy as np
import pandas as pd

class RNNForecaster:
    def __init__(self, sequence_length=30, units=50, dropout_rate=0.2, epochs=50, batch_size=32):
        self.sequence_length = sequence_length
        self.units = units
        self.dropout_rate = dropout_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self.model = None
        self.scaler_X = None
        self.scaler_y = None
        self.features_to_scale = None
        self.target = 'energy_kwh'

    def _build_model(self, input_shape):

        self.model = Sequential([
            tf.keras.layers.Input(shape=input_shape), # Add this Input layer
            SimpleRNN(self.units, activation='relu'), # RNN layer
            Dropout(self.dropout_rate), # Dropout layer
            Dense(1) # Dense layer
        ])
        self.model.compile(optimizer='adam', loss='mean_squared_error') # Compile the model
        print("RNN model built.")

    def train(self, X_train_raw, y_train_raw):

        # Scale features and target
        self.features_to_scale = X_train_raw.columns.tolist()
        
        self.scaler_X = MinMaxScaler()
        X_train_scaled = self.scaler_X.fit_transform(X_train_raw[self.features_to_scale])

        self.scaler_y = MinMaxScaler()
        y_train_scaled = self.scaler_y.fit_transform(y_train_raw.values.reshape(-1, 1))

        # Create sequences
        X_train_seq, y_train_seq = self._create_sequences(pd.DataFrame(X_train_scaled, columns=self.features_to_scale, index=X_train_raw.index),
                                                         pd.Series(y_train_scaled.flatten(), index=y_train_raw.index))
        
        self._build_model((X_train_seq.shape[1], X_train_seq.shape[2]))
        
        print("Training RNN model...")
        self.model.fit(X_train_seq, y_train_seq, epochs=self.epochs, batch_size=self.batch_size, verbose=1)
        print("RNN model trained.")

    def predict(self, X_test_raw, y_test_raw):

        if self.model is None or self.scaler_X is None or self.scaler_y is None:
            raise ValueError("Model has not been trained yet. Call .train() first.")

        # Scale features and target
        X_test_scaled = self.scaler_X.transform(X_test_raw[self.features_to_scale])
        y_test_scaled = self.scaler_y.transform(y_test_raw.values.reshape(-1, 1))

        # Create sequences
        X_test_seq, y_test_seq_true = self._create_sequences(pd.DataFrame(X_test_scaled, columns=self.features_to_scale, index=X_test_raw.index),
                                                             pd.Series(y_test_scaled.flatten(), index=y_test_raw.index))

        predictions_scaled = self.model.predict(X_test_seq)
        predictions = self.scaler_y.inverse_transform(predictions_scaled)
        y_true = self.scaler_y.inverse_transform(y_test_seq_true.reshape(-1, 1))
        
        return y_true.flatten(), predictions.flatten()

    def evaluate(self, y_true, y_pred):

        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mape = mean_absolute_percentage_error(y_true, y_pred)
        print(f"RNN Model Evaluation:")
        print(f"  MAE: {mae:.2f}")
        print(f"  RMSE: {rmse:.2f}")
        print(f"  MAPE: {mape:.2f}%")
        return {'mae': mae, 'rmse': rmse, 'mape': mape}

    def _create_sequences(self, data_scaled_df, target_scaled_series):
 
        data = pd.concat([data_scaled_df, target_scaled_series.rename(self.target)], axis=1)
        xs, ys = [], []
        for i in range(len(data) - self.sequence_length):
            x = data.iloc[i:(i + self.sequence_length)][self.features_to_scale].values
            y = data.iloc[i + self.sequence_length][self.target]
            xs.append(x)
            ys.append(y)
        return np.array(xs), np.array(ys)