
from src.data_preprocessing import (
    load_energy_data,
    load_weather_data,
    preprocess_energy_data,
    preprocess_weather_data,
    merge_data,
    create_time_series_features,
    train_test_split_time_series,
    create_sequences
)
from src.models.xgboost_model import XGBoostForecaster
from src.models.lightgbm_model import LightGBMForecaster
from src.models.rnn_model import RNNForecaster
from src.models.lstm_model import LSTMForecaster
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def run_forecasting_pipeline():
    # 1. Load data
    df_energy = load_energy_data()
    df_weather = load_weather_data()

    if df_energy is None or df_weather is None:
        print("Exiting pipeline due to data loading errors.")
        return

    # 2. Preprocess data
    daily_energy_consumption = preprocess_energy_data(df_energy.copy())
    df_weather_processed = preprocess_weather_data(df_weather.copy())

    if daily_energy_consumption is None or df_weather_processed is None:
        print("Exiting pipeline due to data preprocessing errors.")
        return

    # 3. Merge data
    df_merged = merge_data(daily_energy_consumption, df_weather_processed)

    if df_merged is None:
        print("Exiting pipeline due to data merging errors.")
        return

    # 4. Create time series features
    df_features = create_time_series_features(df_merged.copy())

    # 5. Define features and target
    target = 'energy_kwh'
    features = [col for col in df_features.columns if col != target]

    # 6. Split data into training and testing sets
    train_df, test_df = train_test_split_time_series(df_features, test_size=0.2)

    X_train, y_train = train_df[features], train_df[target]
    X_test, y_test = test_df[features], test_df[target]

    print(f"X_train shape: {X_train.shape}, y_train shape: {y_train.shape}")
    print(f"X_test shape: {X_test.shape}, y_test shape: {y_test.shape}")

    # --- XGBoost Model ---
    print("\n--- Running XGBoost Model ---")
    xgboost_forecaster = XGBoostForecaster()
    xgboost_forecaster.train(X_train, y_train)
    xgboost_predictions = xgboost_forecaster.predict(X_test)
    xgboost_metrics = xgboost_forecaster.evaluate(y_test, xgboost_predictions)
  
    # --- LightGBM Model ---
    print("\n--- Running LightGBM Model ---")
    lightgbm_forecaster = LightGBMForecaster()
    lightgbm_forecaster.train(X_train, y_train)
    lightgbm_predictions = lightgbm_forecaster.predict(X_test)
    lightgbm_metrics = lightgbm_forecaster.evaluate(y_test, lightgbm_predictions)

    # --- RNN Model ---
    print("\n--- Running RNN Model ---")
    # For RNN/LSTM, adjust sequence_length based on your data and desired look-back
    # Note: X_test needs to include enough previous steps for sequence creation
    rnn_forecaster = RNNForecaster(sequence_length=30, epochs=50, batch_size=32)
    rnn_forecaster.train(X_train, y_train)
    # RNN predict returns y_true_seq and predictions_seq for easier comparison
    rnn_y_true, rnn_predictions = rnn_forecaster.predict(X_test, y_test)
    rnn_metrics = rnn_forecaster.evaluate(rnn_y_true, rnn_predictions)

    # --- LSTM Model ---
    print("\n--- Running LSTM Model ---")
    lstm_forecaster = LSTMForecaster(sequence_length=30, epochs=50, batch_size=32)
    lstm_forecaster.train(X_train, y_train)
    # LSTM predict returns y_true_seq and predictions_seq for easier comparison
    lstm_y_true, lstm_predictions = lstm_forecaster.predict(X_test, y_test)
    lstm_metrics = lstm_forecaster.evaluate(lstm_y_true, lstm_predictions)

    # Plotting results
    plt.figure(figsize=(15, 7))
    plt.plot(y_test.index, y_test, label='Actual Energy Consumption')
    plt.plot(y_test.index, xgboost_predictions, label='XGBoost Predictions', alpha=0.7)
    plt.plot(y_test.index, lightgbm_predictions, label='LightGBM Predictions', alpha=0.7)
    
    # For RNN/LSTM, the index for predictions will be shifted due to sequence length
    rnn_plot_index = y_test.index[rnn_forecaster.sequence_length:]
    lstm_plot_index = y_test.index[lstm_forecaster.sequence_length:]

    if len(rnn_plot_index) == len(rnn_predictions):
        plt.plot(rnn_plot_index, rnn_predictions, label='RNN Predictions', alpha=0.7)
    else:
        print("RNN prediction length mismatch for plotting. Skipping RNN plot.")

    if len(lstm_plot_index) == len(lstm_predictions):
        plt.plot(lstm_plot_index, lstm_predictions, label='LSTM Predictions', alpha=0.7)
    else:
        print("LSTM prediction length mismatch for plotting. Skipping LSTM plot.")
 
    plt.title('Energy Consumption Forecasting - Actual vs. Predicted')
    plt.xlabel('Date')
    plt.ylabel('Energy (KWH)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    run_forecasting_pipeline()