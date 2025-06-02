import pytest
import pandas as pd
import numpy as np
from src.models.rnn_model import RNNForecaster
import tensorflow as tf

@pytest.fixture
def sample_data_rnn():
    # Generate some synthetic data for testing RNN
    dates = pd.to_datetime(pd.date_range(start='2020-01-01', periods=100))
    X = pd.DataFrame(np.random.rand(100, 3), columns=[f'feature_{i}' for i in range(3)], index=dates)
    y = pd.Series(np.random.rand(100) * 100 + 50, index=dates, name='energy_kwh') # Ensure positive values for MAPE
    return X, y

def test_rnn_forecaster_init():
    forecaster = RNNForecaster(sequence_length=10)
    assert forecaster.sequence_length == 10
    assert forecaster.units == 50

def test_rnn_forecaster_train_predict(sample_data_rnn):
    X_raw, y_raw = sample_data_rnn
    # Need sufficient data for sequence creation
    if len(X_raw) < 60: 
        pytest.skip("Not enough data for sequence creation and train-test split.")

    X_train_raw, y_train_raw = X_raw.iloc[:80], y_raw.iloc[:80]
    X_test_raw, y_test_raw = X_raw.iloc[80:], y_raw.iloc[80:]

    forecaster = RNNForecaster(sequence_length=10, epochs=2) 
    forecaster.train(X_train_raw, y_train_raw)
    y_true_ret, predictions = forecaster.predict(X_test_raw, y_test_raw)

    expected_len = len(y_test_raw) - forecaster.sequence_length
    assert len(predictions) == expected_len
    assert len(y_true_ret) == expected_len
    assert isinstance(predictions, np.ndarray)
    assert np.all(predictions >= 0) 

def test_rnn_forecaster_evaluate(sample_data_rnn):
    X_raw, y_raw = sample_data_rnn
    if len(X_raw) < 60:
        pytest.skip("Not enough data for sequence creation and train-test split.")

    X_train_raw, y_train_raw = X_raw.iloc[:80], y_raw.iloc[:80]
    X_test_raw, y_test_raw = X_raw.iloc[80:], y_raw.iloc[80:]

    forecaster = RNNForecaster(sequence_length=10, epochs=2)
    forecaster.train(X_train_raw, y_train_raw)
    y_true_ret, predictions = forecaster.predict(X_test_raw, y_test_raw)
    metrics = forecaster.evaluate(y_true_ret, predictions)

    assert 'mae' in metrics
    assert 'rmse' in metrics
    assert 'mape' in metrics
    assert isinstance(metrics['mae'], float)
    assert isinstance(metrics['rmse'], float)
    assert isinstance(metrics['mape'], float)

def test_rnn_forecaster_predict_before_train(sample_data_rnn):
    X_test_raw, y_test_raw = sample_data_rnn[0].iloc[80:], sample_data_rnn[1].iloc[80:]
    forecaster = RNNForecaster(sequence_length=10)
    with pytest.raises(ValueError, match="Model has not been trained yet."):
        forecaster.predict(X_test_raw, y_test_raw)