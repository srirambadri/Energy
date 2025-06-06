import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.metrics import root_mean_squared_error as rmse_score
import matplotlib.pyplot as plt

def calculate_error_metrics(y_true, y_pred, name=""):

    # Align indices and drop NaNs for consistent comparison
    y_true = pd.Series(y_true).dropna()
    y_pred = pd.Series(y_pred).reindex(y_true.index).dropna()

    if y_true.empty or y_pred.empty or len(y_true) != len(y_pred):
        print(f"Warning: Insufficient or misaligned data for error calculation ({name}). Skipping metrics.")
        return {'mse': np.nan, 'rmse': np.nan, 'mae': np.nan, 'r2': np.nan}

    # Compute the mean squared error.
    mse = mean_squared_error(y_true, y_pred)
    
    # Compute the root mean squared error.
    rmse = rmse_score(y_true, y_pred)
    
    # Compute the mean absolute error.
    mae = mean_absolute_error(y_true, y_pred)
    
    # Compute the coefficient of determination (R-squared).
    r2 = r2_score(y_true, y_pred)
    
    # Print the error metrics.
    if name:
        print(f"  --- {name} Error Metrics ---")
    print(f"  Mean Squared Error (MSE): {mse:.4f}") 
    print(f"  Root Mean Squared Error (RMSE): {rmse:.4f}")
    print(f"  Mean Absolute Error (MAE): {mae:.4f}")
    print(f"  Coefficient of Determination (R-squared): {r2:.4f}")

    return {'mse': mse, 'rmse': rmse, 'mae': mae, 'r2': r2}

def calculate_profits(df_with_forecasts, accepted_bids_second, accepted_bids_first, actual_data, taxes_per_mwh=10):

    if df_with_forecasts is None or accepted_bids_second is None or actual_data is None or accepted_bids_first is None:
        print("One or more input DataFrames for profit calculation are None.")
        return {}

    # Expected profit before taxes
    Expected_profit_before_taxes_series = (df_with_forecasts['diff'] * accepted_bids_second["trading_volume"]).fillna(0)
    Expected_profit_before_taxes_sum = Expected_profit_before_taxes_series.sum()
    print(f"\nExpected profit before taxes : {Expected_profit_before_taxes_sum:.2f}")

    # Expected profit after taxes
    Expected_profit_after_taxes_series = ((df_with_forecasts["diff"] - taxes_per_mwh) * accepted_bids_second["trading_volume"]).fillna(0)
    Expected_profit_after_taxes_sum = Expected_profit_after_taxes_series.sum()
    print(f"Expected profit after taxes : {Expected_profit_after_taxes_sum:.2f}")

    # Actual profit before taxes
    Actual_profit_before_taxes_series = (actual_data['diff'] * accepted_bids_second["trading_volume"]).fillna(0)
    Actual_profit_before_taxes_sum = Actual_profit_before_taxes_series.sum()
    print(f"\nActual profit before taxes : {Actual_profit_before_taxes_sum:.2f}")

    # Actual profit after taxes
    Actual_profit_after_taxes_series = ((actual_data["diff"] - taxes_per_mwh) * accepted_bids_second["trading_volume"]).fillna(0)
    Actual_profit_after_taxes_sum = Actual_profit_after_taxes_series.sum()
    print(f"Actual profit after taxes : {Actual_profit_after_taxes_sum:.2f}")

    # Profit/loss from the system price
    # Ensure system_price is aligned with the trading data's index
    system_price_aligned = actual_data.loc[accepted_bids_second.index, 'system_price'].fillna(0)

    System_price_profit_series = system_price_aligned * (accepted_bids_second["trading_volume"] - accepted_bids_first["trading_volume"]).fillna(0)
    System_price_profit_sum = System_price_profit_series.sum()
    print(f"\nActual profit/loss from system price : {System_price_profit_sum:.2f}")

    return {
        'expected_profit_before_taxes_sum': Expected_profit_before_taxes_sum,
        'expected_profit_after_taxes_sum': Expected_profit_after_taxes_sum,
        'actual_profit_before_taxes_sum': Actual_profit_before_taxes_sum,
        'actual_profit_after_taxes_sum': Actual_profit_after_taxes_sum,
        'system_price_profit_loss_sum': System_price_profit_sum,
        'expected_profit_before_taxes_series': Expected_profit_before_taxes_series,
        'expected_profit_after_taxes_series': Expected_profit_after_taxes_series,
        'actual_profit_before_taxes_series': Actual_profit_before_taxes_series,
        'actual_profit_after_taxes_series': Actual_profit_after_taxes_series
    }

def evaluate_forecasts_and_profits(auction_data_test, forecast_auctions, individual_forecasts,
                                   Actual_profit_before_taxes_series, Expected_profit_before_taxes_series,
                                   Actual_profit_after_taxes_series, Expected_profit_after_taxes_series):

    all_metrics = {}
    model_names = ['ARIMA', 'XGBoost', 'LinearRegression', 'Lasso', 'MLPRegressor']

    print("\n--- Evaluation of Price Forecasts ---")
    print("\nError for First Auction Price Forecasting:")
    all_metrics['first_auction_price_forecast'] = calculate_error_metrics(
        auction_data_test['price_first_auction'], forecast_auctions['forecast_price_first_auction'],
        name="First Auction Price Forecast"
    )

    print("\nError for Second Auction Price Forecasting (Averaged Model):")
    all_metrics['second_auction_price_forecast_averaged'] = calculate_error_metrics(
        auction_data_test['price_second_auction'], forecast_auctions['forecast_price_second_auction'],
        name="Second Auction Price Forecast (Averaged)"
    )
    
    print("\nError for Second Auction Price Forecasting (Individual Models):")
    for model_name in model_names:
        key_name = f"{model_name}_forecast_price_second_auction"
        if key_name in individual_forecasts:
            print(f"\nError for {model_name} on Second Auction Price:")
            all_metrics[f'second_auction_price_forecast_{model_name.lower()}'] = calculate_error_metrics(
                auction_data_test['price_second_auction'], individual_forecasts[key_name],
                name=f"{model_name} Second Auction Price Forecast"
            )
        else:
            print(f"  Individual forecast for {model_name} not found or generated. Skipping.")

    print("\n--- Evaluation of Trading Strategy Profits ---")
    print("\nProfit before taxes error:")
    all_metrics['profit_before_taxes_error'] = calculate_error_metrics(
        Actual_profit_before_taxes_series, Expected_profit_before_taxes_series,
        name="Profit Before Taxes"
    )

    print("\nProfit AFTER taxes error:")
    all_metrics['profit_after_taxes_error'] = calculate_error_metrics(
        Actual_profit_after_taxes_series, Expected_profit_after_taxes_series,
        name="Profit After Taxes"
    )
    
    return all_metrics

def plot_results(actual_prices, forecast_prices, title="Actual vs. Expected Auction Prices"):

    if actual_prices is None or forecast_prices is None:
        print("Cannot plot: Actual or forecast price data is None.")
        return

    plt.figure(figsize=(15, 7))
    plt.plot(actual_prices.index, actual_prices, label='Actual Price', color='blue')
    plt.plot(forecast_prices.index, forecast_prices, label='Expected Price', color='red', linestyle='--')
    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()