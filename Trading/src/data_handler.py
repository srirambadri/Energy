import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

def convert_to_float(value):

    try:
        if isinstance(value, str) and '-' in value:
            if value.endswith('-'):
                return -1.0 * float(value.replace('-', ''))
            elif value.startswith('-'):
                return float(value)
            else:
                return np.nan 
        else:
            return float(value)
    except (ValueError, TypeError):
        return np.nan

def preprocess_dataframe(df):

    try:
        df.index = pd.to_datetime(df.index, format='[%d/%m/%Y %H:%M]')
    except ValueError:
        df.index = pd.to_datetime(df.index)

    if 'NaT' in df.index:
        df = df.drop('NaT')

    df = df.applymap(convert_to_float)

    df = df[~df.index.duplicated()]

    df = df.resample('H').asfreq()

    df = df.interpolate(method='linear')
    
    return df

def load_and_preprocess_data(auction_filepath, forecast_filepath, system_filepath):

    try:
        auction_data_raw = pd.read_csv(auction_filepath, sep=';', skiprows=0, index_col=0, parse_dates=True, dayfirst=True)
        forecast_inputs_raw = pd.read_csv(forecast_filepath, sep=';', skiprows=0, index_col=0, parse_dates=True, dayfirst=True)
        system_prices_raw = pd.read_csv(system_filepath, sep=';', skiprows=0, index_col=0, parse_dates=True, dayfirst=True)

        auction_data = preprocess_dataframe(auction_data_raw.copy())
        forecast_inputs = preprocess_dataframe(forecast_inputs_raw.copy())
        system_prices = preprocess_dataframe(system_prices_raw.copy())

        print("Data loaded and preprocessed successfully.")
        return auction_data, forecast_inputs, system_prices
    except FileNotFoundError as e:
        print(f"Error loading file: {e}. Please ensure data files are in the 'data/' directory.")
        return None, None, None
    except Exception as e:
        print(f"An unexpected error occurred during data loading and preprocessing: {e}")
        return None, None, None

def split_data(auction_data, forecast_inputs, system_prices, split_date='2022-03-01'):

    if auction_data is None or forecast_inputs is None or system_prices is None:
        print("Input dataframes are None. Cannot split data.")
        return None, None, None, None, None, None

    auction_data_train = auction_data.loc[auction_data.index < split_date]
    auction_data_test = auction_data.loc[auction_data.index >= split_date]

    forecast_inputs_train = forecast_inputs.loc[forecast_inputs.index < split_date]
    forecast_inputs_test = forecast_inputs.loc[forecast_inputs.index >= split_date]

    system_prices_train = system_prices.loc[system_prices.index < split_date]
    system_prices_test = system_prices.loc[system_prices.index >= split_date]

    print(f"Data split into training and testing sets based on {split_date}.")
    return (auction_data_train, auction_data_test,
            forecast_inputs_train, forecast_inputs_test,
            system_prices_train, system_prices_test)