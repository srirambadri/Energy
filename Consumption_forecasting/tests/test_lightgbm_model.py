import pytest
import pandas as pd
import numpy as np
import lightgbm as lgb
from src.models.lightgbm_model import LightGBMForecaster

@pytest.fixture
def sample_data():
    # Generate some synthetic data for testing
    dates = pd.to_datetime(pd.date_range(start='2020-01-01', periods=100))
    X = pd.DataFrame(np.random.rand(100, 5), columns=[f'feature_{i}' for i in range(5)], index=dates)
    y = pd.Series(np.random.rand(100) * 100, index=dates, name='energy_kwh')
    return X, y

def test_lightgbm_forecaster_init():
    forecaster = LightGBMForecaster()
    assert isinstance(forecaster.model, lgb.LGBMRegressor)

def test_lightgbm_forecaster_train_predict(sample_data):
    X, y = sample_data
    X_train, y_train = X.iloc[:80], y.iloc[:80]
    X_test, y_test = X.iloc[80:], y.iloc[80:]

    forecaster = LightGBMForecaster()
    forecaster.train(X_train, y_train)
    predictions = forecaster.predict(X_test)

    assert len(predictions) == len(y_test)
    assert isinstance(predictions, np.ndarray)

def test_lightgbm_forecaster_evaluate(sample_data):
    X, y = sample_data
    X_train, y_train = X.iloc[:80], y.iloc[:80]
    X_test, y_test = X.iloc[80:], y.iloc[80:]

    forecaster = LightGBMForecaster()
    forecaster.train(X_train, y_train)
    predictions = forecaster.predict(X_test)
    metrics = forecaster.evaluate(y_test, predictions)

    assert 'mae' in metrics
    assert 'rmse' in metrics
    assert 'mape' in metrics
    assert isinstance(metrics['mae'], float)
    assert isinstance(metrics['rmse'], float)
    assert isinstance(metrics['mape'], float)

def test_lightgbm_forecaster_predict_before_train(sample_data):
    X, y = sample_data
    X_test = X.iloc[80:]
    forecaster = LightGBMForecaster()
    with pytest.raises(ValueError, match="Model has not been trained yet."):
        forecaster.predict(X_test)