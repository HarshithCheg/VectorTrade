import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit

TICKER = "GOOGL"

FEATURE = ["returns_1d", "returns_5d", "returns_10d", "close_to_sma20", "close_to_sma50", "volatility_10d", "volume_ratio", "hl_range", "rsi_14"]

def predict(model, X_test, df):
    prediction = model.predict(X_test)
    dates = df.loc[X_test.index, "Date"]
    result = pd.DataFrame({"Date": dates, "Predicted": prediction})
    print(result.tail(10))
    return result

def calc_rsi(close, period=14):
    #rsi - Relative Strength Index: stock is overbought or oversold on a scale of 100
    #rsi > 70: overbought, price will likely drop
    #rsi < 30: oversold, price will likely rise
    change = close.diff()
    # gain = change.apply(lambda x: x if x > 0 else 0).rolling(period).mean()
    gain = change.clip(lower=0).rolling(period).mean() #this vectorized and way faster
    # loss = -change.apply(lambda x: x if x < 0 else 0).rolling(period).mean()
    loss = (-change.clip(upper=0)).rolling(period).mean() 
    rs = gain/loss.replace(0, 1e-10)
    return 100 - (100/(1+rs))
