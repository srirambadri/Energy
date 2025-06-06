import pandas as pd
import numpy as np

def calculate_trading_volume(forecast_auctions_df):
    """
    Computes the safe trading volume to ensure a zero net position.
    This is done by selecting the minimum trading volume between the two auctions.

    Parameters:
        forecast_auctions_df (pd.DataFrame): DataFrame containing forecasted traded volumes.

    Returns:
        pd.DataFrame: The input DataFrame with a new 'trading_volume_for_both_auctions' column.
    """
    if forecast_auctions_df is None:
        print("Input DataFrame for trading volume calculation is None.")
        return None

    forecast_auctions_df['trading_volume_for_both_auctions'] = \
        forecast_auctions_df[['forecast_traded_volume_first_auction', 'forecast_traded_volume_second_auction']].min(axis=1)
    
    print("Trading volume calculated.")
    return forecast_auctions_df

def make_initial_trading_decision(forecast_auctions_df, taxes_per_mwh=20):
    """
    Compares the prices of the two auctions to make an initial trading decision
    (Buy, Sell, or Hold) for the first auction. The decision is then reversed for the second auction.

    Parameters:
        forecast_auctions_df (pd.DataFrame): DataFrame with forecasted prices.
        taxes_per_mwh (float): Taxes and fees per MWh.

    Returns:
        pd.DataFrame: The input DataFrame with 'first_auction_sell_buy',
                      'second_auction_sell_buy', and 'diff' columns.
    """
    if forecast_auctions_df is None:
        print("Input DataFrame for trading decision is None.")
        return None

    taxes = taxes_per_mwh # Original notebook had 10 * 2, assuming 10 is a base tax and 2 for two auctions.

    forecast_auctions_df['first_auction_sell_buy'] = np.where(
        forecast_auctions_df['forecast_price_first_auction'] + taxes < forecast_auctions_df['forecast_price_second_auction'],
        'Buy electricity',
        np.where(
            forecast_auctions_df['forecast_price_first_auction'] > forecast_auctions_df['forecast_price_second_auction'] + taxes,
            'Sell electricity',
            'Hold'
        )
    )

    forecast_auctions_df['second_auction_sell_buy'] = forecast_auctions_df['first_auction_sell_buy'].replace(
        {'Buy electricity': 'Sell electricity', 'Sell electricity': 'Buy electricity', 'Hold': 'Hold'}
    )

    # Calculate the expected profit per MWh
    forecast_auctions_df['diff'] = np.where(
        forecast_auctions_df['first_auction_sell_buy'] == 'Sell electricity',
        forecast_auctions_df['forecast_price_first_auction'] - forecast_auctions_df['forecast_price_second_auction'],
        np.where(
            forecast_auctions_df['first_auction_sell_buy'] == 'Buy electricity',
            forecast_auctions_df['forecast_price_second_auction'] - forecast_auctions_df['forecast_price_first_auction'],
            0
        )
    )
    
    # Fill any NaN values that might arise from 'diff' calculation with 0
    forecast_auctions_df = forecast_auctions_df.fillna(0)

    print("Initial trading decisions made.")
    return forecast_auctions_df

def generate_first_auction_bids(forecast_auctions_df, risk_percentage=0.05):
    """
    Creates and adjusts the first auction bids based on forecasted prices,
    trading volume, and a defined risk percentage.

    Parameters:
        forecast_auctions_df (pd.DataFrame): DataFrame with forecasted data and trading decisions.
        risk_percentage (float): The percentage of expected profit used to adjust trading price.

    Returns:
        pd.DataFrame: DataFrame containing the first auction bids (trading_price, trading_volume, action).
    """
    if forecast_auctions_df is None:
        print("Input DataFrame for first auction bids is None.")
        return None

    first_auction_bids = forecast_auctions_df[['forecast_price_first_auction', 'trading_volume_for_both_auctions', 'first_auction_sell_buy']].copy()
    first_auction_bids = first_auction_bids.rename(columns={
        "forecast_price_first_auction": "trading_price",
        "trading_volume_for_both_auctions": "trading_volume",
        "first_auction_sell_buy": "action"
    })

    # Adjust the first auction trading price based on the risk percentage.
    # If selling, lower the price by (diff * risk_percentage) to increase acceptance probability.
    # If buying, raise the price by (diff * risk_percentage) to increase acceptance probability.
    first_auction_bids['trading_price'] = np.where(
        first_auction_bids['action'] == 'Sell electricity',
        first_auction_bids['trading_price'] - (forecast_auctions_df['diff'] * risk_percentage),
        np.where(
            first_auction_bids['action'] == 'Buy electricity',
            first_auction_bids['trading_price'] + (forecast_auctions_df['diff'] * risk_percentage),
            0
        )
    )

    # If action is 'Hold', set trading price and volume to 0
    first_auction_bids.loc[first_auction_bids['action'] == "Hold", ['trading_price', 'trading_volume']] = 0
    
    print("First auction bids generated.")
    return first_auction_bids

def determine_accepted_first_auction_bids(first_auction_bids, actual_auction_data):
    """
    Determines which first auction bids are accepted based on bid price vs. actual clearing price.

    Parameters:
        first_auction_bids (pd.DataFrame): DataFrame of generated first auction bids.
        actual_auction_data (pd.DataFrame): DataFrame containing actual auction prices and volumes.

    Returns:
        pd.DataFrame: A modified DataFrame of accepted bids for the first auction,
                      with prices set to clearing prices and volumes adjusted.
    """
    if first_auction_bids is None or actual_auction_data is None:
        print("Input DataFrame for accepted bids (first auction) is None.")
        return None

    accepted = pd.Series(False, index=first_auction_bids.index)

    # Bids for 'Hold' are never accepted
    accepted.loc[first_auction_bids['action'] == "Hold"] = False

    # Selling bids are accepted if bid price <= actual price
    accepted.loc[first_auction_bids['action'] == "Sell electricity"] = (
        actual_auction_data.loc[first_auction_bids['action'] == "Sell electricity", 'price_first_auction'] >= 
        first_auction_bids.loc[first_auction_bids['action'] == "Sell electricity", 'trading_price']
    )

    # Buying bids are accepted if bid price >= actual price
    accepted.loc[first_auction_bids['action'] == "Buy electricity"] = (
        actual_auction_data.loc[first_auction_bids['action'] == "Buy electricity", 'price_first_auction'] <= 
        first_auction_bids.loc[first_auction_bids['action'] == "Buy electricity", 'trading_price']
    )

    accepted = accepted.replace({True: 'accepted', False: 'unaccepted'})

    accepted_bids_first = first_auction_bids.copy()

    # Set unaccepted bids to 'Hold' with zero price and volume
    accepted_bids_first.loc[accepted == "unaccepted", 'action'] = "Hold"
    accepted_bids_first.loc[accepted_bids_first['action'] == "Hold", ['trading_price', 'trading_volume']] = 0

    # Adjust trading volume to the minimum of bid volume and actual traded volume
    accepted_bids_first.loc[accepted_bids_first['action'] != "Hold", 'trading_volume'] = np.minimum(
        accepted_bids_first.loc[accepted_bids_first['action'] != "Hold", 'trading_volume'],
        actual_auction_data.loc[accepted_bids_first['action'] != "Hold", 'traded_volume_first_auction']
    )

    # Set trading price to the actual clearing price for accepted bids
    accepted_bids_first.loc[accepted_bids_first['action'] == "Buy electricity", 'trading_price'] = \
        actual_auction_data.loc[accepted_bids_first['action'] == "Buy electricity", 'price_first_auction']
    accepted_bids_first.loc[accepted_bids_first['action'] == "Sell electricity", 'trading_price'] = \
        actual_auction_data.loc[accepted_bids_first['action'] == "Sell electricity", 'price_first_auction']
        
    print("Accepted first auction bids determined.")
    return accepted_bids_first

def generate_second_auction_bids(accepted_bids_first, forecast_auctions_df, actual_auction_data):
    """
    Generates bids for the second auction, ensuring a zero net position.
    Accepted bids from the first auction are effectively "retracted" and opposing bids
    are placed in the second auction.

    Parameters:
        accepted_bids_first (pd.DataFrame): DataFrame of accepted bids from the first auction.
        forecast_auctions_df (pd.DataFrame): DataFrame with forecasted data.
        actual_auction_data (pd.DataFrame): DataFrame containing actual auction prices and volumes.

    Returns:
        pd.DataFrame: A modified DataFrame of accepted bids for the second auction.
    """
    if accepted_bids_first is None or forecast_auctions_df is None or actual_auction_data is None:
        print("One or more input DataFrames for second auction bids are None.")
        return None

    second_auction_bids = accepted_bids_first.copy()

    # Reverse the action for the second auction for accepted first auction bids
    second_auction_bids['action'] = second_auction_bids['action'].replace(
        {'Buy electricity': 'Sell electricity', 'Sell electricity': 'Buy electricity', 'Hold': 'Hold'}
    )

    # Adjust price for second auction bids to ensure acceptance (pay-as-cleared mechanism)
    # Set selling price much lower and buying price much higher than expected
    second_auction_bids.loc[second_auction_bids['action'] == "Sell electricity", "trading_price"] = \
        forecast_auctions_df.loc[second_auction_bids['action'] == "Sell electricity", "forecast_price_second_auction"] * 0.1
    second_auction_bids.loc[second_auction_bids['action'] == "Buy electricity", "trading_price"] = \
        forecast_auctions_df.loc[second_auction_bids['action'] == "Buy electricity", "forecast_price_second_auction"] * 10
    
    # Determine acceptance for second auction bids
    accepted_second = pd.Series(False, index=second_auction_bids.index)

    accepted_second.loc[second_auction_bids['action'] == "Hold"] = False

    accepted_second.loc[second_auction_bids['action'] == "Sell electricity"] = (
        actual_auction_data.loc[second_auction_bids['action'] == "Sell electricity" , 'price_second_auction'] >= 
        second_auction_bids.loc[second_auction_bids['action'] == "Sell electricity" , 'trading_price']
    )

    accepted_second.loc[second_auction_bids['action'] == "Buy electricity"] = (
        actual_auction_data.loc[second_auction_bids['action'] == "Buy electricity" , 'price_second_auction'] <= 
        second_auction_bids.loc[second_auction_bids['action'] == "Buy electricity" , 'trading_price']
    )

    accepted_second = accepted_second.replace({True: 'accepted', False: 'unaccepted'})

    # Apply acceptance status to second_auction_bids. Unaccepted bids become 'Hold' with 0 price/volume.
    accepted_bids_second = second_auction_bids.copy()
    accepted_bids_second.loc[accepted_second == "unaccepted"] = [0, 0, "Hold"] # Sets trading_price, trading_volume, action
    
    print("Second auction bids generated and acceptance determined.")
    return accepted_bids_second