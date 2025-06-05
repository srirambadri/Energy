## Description

A ML-based methodology to forecast energy futures prices and volume, and subsequently develop a trading algorithm aimed at maximizing profits in the volatile energy market. It leverages historical auction data from the UK energy market to train and evaluate the models' performance.


## Project Overview

The approach is structured around four main stages:

- Data Preprocessing: Cleaning, interpolating, and splitting historical UK auction data.

- Price Forecasting: Predicting future electricity prices and volumes using various models.

- Trading Decision-Making: Implementing a non-physical financial trading strategy based on forecasts to achieve a zero net position.

- Backtesting & Evaluation: Assessing model accuracy and strategy profitability using standard metrics.


## Key Findings

The trading algorithm's reliance on precise forecasts is crucial, as overestimation or underestimation of auction prices can result in actual profits falling short of expectations, potentially impacting investor confidence and reputation. Model Averaging was identified as the most suitable forecasting model for this task.
