import pandas as pd
import numpy as np

def load_energy_data(filepath='data/london_energy.csv'):

    try:
        df_energy = pd.read_csv(filepath)
        print(f"Successfully loaded energy data from {filepath}")
        return df_energy
    except FileNotFoundError:
        print(f"Error: Energy data file not found at {filepath}")
        return None
    except Exception as e:
        print(f"Error loading energy data: {e}")
        return None

def load_weather_data(filepath='data/london_weather.csv'):

    try:
        df_weather = pd.read_csv(filepath)
        print(f"Successfully loaded weather data from {filepath}")
        return df_weather
    except FileNotFoundError:
        print(f"Error: Weather data file not found at {filepath}")
        return None
    except Exception as e:
        print(f"Error loading weather data: {e}")
        return None

def preprocess_energy_data(df_energy):

    if df_energy is None:
        return None

    df_energy = df_energy.rename(columns={'KWH': 'energy_kwh'})
    df_energy['Date'] = pd.to_datetime(df_energy['Date'])
    df_energy = df_energy.set_index('Date')

    # Handle missing values
    df_energy = df_energy.fillna(method='ffill').fillna(method='bfill') 

    # Remove duplicate dates 
    df_energy = df_energy.groupby(['LCLid', df_energy.index]).agg({'energy_kwh': 'mean'}).reset_index()
    df_energy = df_energy.rename(columns={'level_1': 'Date'}).set_index('Date')

    # Aggregate daily energy consumption 
    daily_energy_consumption = df_energy.groupby('Date')['energy_kwh'].sum().reset_index()
    daily_energy_consumption = daily_energy_consumption.set_index('Date')

    print("Energy data preprocessed.")
    return daily_energy_consumption

def preprocess_weather_data(df_weather):

    if df_weather is None:
        return None

    df_weather['date'] = pd.to_datetime(df_weather['date'].astype(str)) # Ensure date is string before conversion
    df_weather = df_weather.set_index('date')
    df_weather = df_weather.rename(columns={
        'cloud_cover': 'cloud_cover',
        'sunshine': 'sunshine',
        'global_radiation': 'global_radiation',
        'max_temp': 'max_temp',
        'mean_temp': 'mean_temp',
        'min_temp': 'min_temp',
        'precipitation': 'precipitation',
        'pressure': 'pressure',
        'snow_depth': 'snow_depth'
    })

    # Handle missing values
    df_weather = df_weather.fillna(method='ffill').fillna(method='bfill')

    print("Weather data preprocessed.")
    return df_weather

def merge_data(df_energy, df_weather):

    if df_energy is None or df_weather is None:
        return None

    df_merged = pd.merge(df_energy, df_weather, left_index=True, right_index=True, how='inner')
    print("Energy and weather data merged.")
    return df_merged

def create_time_series_features(df):

    if df is None:
        return None

    df['year'] = df.index.year
    df['month'] = df.index.month
    df['day'] = df.index.day
    df['day_of_week'] = df.index.dayofweek
    df['day_of_year'] = df.index.dayofyear
    df['week_of_year'] = df.index.isocalendar().week.astype(int)
    df['quarter'] = df.index.quarter
    print("Time series features created.")
    return df

def train_test_split_time_series(df, test_size=0.2):

    if df is None:
        return None

    train_size = int(len(df) * (1 - test_size))
    train_df = df.iloc[:train_size]
    test_df = df.iloc[train_size:]
    print(f"Data split into training ({len(train_df)} samples) and testing ({len(test_df)} samples).")
    return train_df, test_df

def create_sequences(data, sequence_length):

    xs, ys = [], []
    for i in range(len(data) - sequence_length):
        x = data.iloc[i:(i + sequence_length)].values
        y = data.iloc[i + sequence_length]['energy_kwh']
        xs.append(x)
        ys.append(y)
    return np.array(xs), np.array(ys)