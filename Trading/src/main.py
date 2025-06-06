import pandas as pd
import numpy as np
import warnings
from data_handler import load_and_preprocess_data, split_data
from forecasting_models import generate_and_average_forecasts, run_forecast_model
from trading_strategy import (
    calculate_trading_volume,
    make_initial_trading_decision,
    generate_first_auction_bids,
    determine_accepted_first_auction_bids,
    generate_second_auction_bids
)
from evaluation import calculate_error_metrics, calculate_profits, evaluate_forecasts_and_profits, plot_results
warnings.filterwarnings("ignore")

def run_energy_trading_pipeline(
    auction_data_path='data/auction_data.csv',
    forecast_inputs_path='data/forecast_inputs.csv',
    system_prices_path='data/system_prices.csv',
    train_test_split_date='2022-03-01',
    taxes_per_mwh=20, # 10 * 2 from notebook
    risk_percentage_first_auction=0.05
):
    print("--- Starting Energy Trading Pipeline ---")

    # 1. Load and preprocess data
    auction_data, forecast_inputs, system_prices = load_and_preprocess_data(
        auction_data_path, forecast_inputs_path, system_prices_path
    )

    if auction_data is None:
        print("Pipeline terminated due to data loading/preprocessing errors.")
        return

    # 2. Split data into training and testing sets
    (auction_data_train, auction_data_test,
     forecast_inputs_train, forecast_inputs_test,
     system_prices_train, system_prices_test) = split_data(
        auction_data, forecast_inputs, system_prices, train_test_split_date
    )
    
    if auction_data_train is None:
        print("Pipeline terminated due to data splitting errors.")
        return

    # 3. Generate and average forecasts
    forecast_auctions, individual_forecasts = generate_and_average_forecasts(
        auction_data_train, auction_data_test,
        forecast_inputs_train, forecast_inputs_test
    )
    
    if forecast_auctions is None:
        print("Pipeline terminated due to forecasting errors.")
        return

    # 4. Implement Trading Strategy
    print("\n--- Implementing Trading Strategy ---")
    df_trading = forecast_auctions.copy()

    # Calculate safe trading volume
    df_trading = calculate_trading_volume(df_trading)
    if df_trading is None: return

    # Make initial trading decisions (buy/sell/hold)
    df_trading = make_initial_trading_decision(df_trading, taxes_per_mwh=taxes_per_mwh)
    if df_trading is None: return

    # Create a dataset for actual values to determine bid acceptance
    actual = auction_data_test.loc[df_trading.index, [
        'price_first_auction', 'price_second_auction',
        'traded_volume_first_auction', 'traded_volume_second_auction'
    ]].copy()
    actual["trading_volume_for_both_auctions"] = actual[['traded_volume_first_auction', 'traded_volume_second_auction']].min(axis=1)
    actual['diff'] = np.where(
        df_trading['first_auction_sell_buy'] == 'Sell electricity',
        actual['price_first_auction'] - actual['price_second_auction'],
        np.where(
            df_trading['first_auction_sell_buy'] == 'Buy electricity',
            actual['price_second_auction'] - actual['price_first_auction'],
            0
        )
    )
    actual = actual.fillna(0)
    actual['system_price'] = system_prices_test.loc[df_trading.index, 'system_price'].fillna(0)


    # Generate and determine accepted bids for the first auction
    first_auction_bids = generate_first_auction_bids(df_trading, risk_percentage=risk_percentage_first_auction)
    if first_auction_bids is None: return
    accepted_bids_first = determine_accepted_first_auction_bids(first_auction_bids, actual)
    if accepted_bids_first is None: return

    # Generate and determine accepted bids for the second auction
    accepted_bids_second = generate_second_auction_bids(accepted_bids_first, df_trading, actual) 
    if accepted_bids_second is None: return 


    # 5. Calculate Expected and Actual Profits
    print("\n--- Calculating Profits ---")
    profit_results = calculate_profits(
        df_trading, accepted_bids_second, accepted_bids_first, actual, taxes_per_mwh=10
    )

    # 6. Evaluate Forecasting and Profit Performance
    print("\n--- Evaluating Performance ---")
    
    evaluation_metrics = evaluate_forecasts_and_profits(
        auction_data_test,
        forecast_auctions,
        individual_forecasts,
        profit_results['actual_profit_before_taxes_series'],
        profit_results['expected_profit_before_taxes_series'],
        profit_results['actual_profit_after_taxes_series'],
        profit_results['expected_profit_after_taxes_series']
    )
    
    print("\n--- Pipeline Finished ---")

    # 7. Results Visualization (Optional - uncomment to show plots)
    print("\n--- Visualizing Results ---")
    plot_results(
        auction_data_test['price_first_auction'],
        forecast_auctions['forecast_price_first_auction'],
        title="First Auction: Actual vs. Forecasted Price"
    )
    plot_results(
        auction_data_test['price_second_auction'],
        forecast_auctions['forecast_price_second_auction'],
        title="Second Auction: Actual vs. Forecasted Price (Averaged Model)"
    )

if __name__ == "__main__":
    run_energy_trading_pipeline()
