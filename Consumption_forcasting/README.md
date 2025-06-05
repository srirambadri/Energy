## Description

- The ability to efficiently forecast hourly energy consumption plays an important role on how energy is distributed and consumed. - London Energy Dataset (London Datastore) which contains the energy consumption of 5,567 randomly selected households in the city of London, UK for the time period of November 2011 to February 2014.
- Additional weather related data to improve prediction (ECA dataset)
- Using Ensemble models: extreme gradient boosting or XGBoost and light gradient boosting or LGB models
- Deep learning algorithms have played vital roles in prediction and forecasting problems 
- Recurrent Neural Networks (RNN) and Long-Term Short Memory (LSTM) are applied with the aim of making forecast on future energy consumption
- Models generally performed better by reducing batch size and by increasing epoch sizes. Results are evaluated using RMSE, MAE and R2 scores

## Project Structure

```bash
Consumption_forecasting/
├── data/
│   ├── london_energy.csv           # Raw energy consumption data
│   └── london_weather.csv          # Raw weather data
├── src/
│   ├── init.py                 
│   ├── data_preprocessing.py       # Handles data loading and preprocessing
│   ├── models/
│   │   ├── init.py             
│   │   ├── xgboost_model.py        # XGBoost forecasting model
│   │   ├── lightgbm_model.py       # LightGBM forecasting model
│   │   ├── rnn_model.py            # Recurrent Neural Network (RNN) forecasting model
│   │   └── lstm_model.py           # Long Short-Term Memory (LSTM) forecasting model
├── tests/
│   ├── init.py                 
│   ├── test_xgboost_model.py       # Unit tests for XGBoost model
│   ├── test_lightgbm_model.py      # Unit tests for LightGBM model
│   ├── test_rnn_model.py           # Unit tests for RNN model
│   └── test_lstm_model.py          # Unit tests for LSTM model
├── notebooks/
│   ├── Energy Consumption Forecasting.ipynb  # Notebook with ML models
│   └── Forecasting with Deep learning.ipynb  # Notebook with DL models          
├── requirements.txt                # Lists project dependencies
└── README.md                       # Project README file
```

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/srirambadri/energy.git
    cd Consumption_forecasting
    ```

2.  **Create a virtual environment (recommended):**

    Use python 3.9 supporting Tensorflow
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Forecasting Pipeline

To run the entire forecasting pipeline (data loading, preprocessing, model training, prediction, and evaluation for all models):
```bash
python main.py
```
To run unit tests on the models
```bash
pytest tests/
```