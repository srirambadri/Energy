import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error
import numpy as np

class XGBoostForecaster:
    def __init__(self, n_estimators=1000, learning_rate=0.05, max_depth=5,
                 subsample=0.7, colsample_bytree=0.7, random_state=42):
        self.model = xgb.XGBRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            subsample=subsample,
            colsample_bytree=colsample_bytree,
            random_state=random_state,
            n_jobs=-1
        )
        self.features = None
        self.target = 'energy_kwh'

    def train(self, X_train, y_train):

        self.features = X_train.columns.tolist()
        self.model.fit(X_train, y_train)
        print("XGBoost model trained.")

    def predict(self, X_test):

        if self.features is None:
            raise ValueError("Model has not been trained yet. Call .train() first.")
        predictions = self.model.predict(X_test[self.features])
        return predictions

    def evaluate(self, y_true, y_pred):

        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mape = mean_absolute_percentage_error(y_true, y_pred)
        print(f"XGBoost Model Evaluation:")
        print(f"  MAE: {mae:.2f}")
        print(f"  RMSE: {rmse:.2f}")
        print(f"  MAPE: {mape:.2f}%")
        return {'mae': mae, 'rmse': rmse, 'mape': mape}