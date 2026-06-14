import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from brain import load_data, features, create_labels, train_model

BASE_DIR = Path(__file__).resolve().parent.parent

FEATURE = ["returns_1d", "returns_5d", "returns_10d", "close_to_sma20", "close_to_sma50", "volatility_10d", "volume_ratio", "hl_range", "rsi_14"]
TICKER = "GOOGL" # only needed if you will be using just src without backend.

def predict(model, X_test, df):
    prediction = model.predict(X_test)
    dates = df.loc[X_test.index, "Date"]
    result = pd.DataFrame({"Date": dates, "Predicted": prediction})
    return result

_model_cache = {}
def load_model(ticker):
    if ticker not in _model_cache:
        path = BASE_DIR/f"models/{ticker}_model.pkl"
        if not path.exists():
            df = load_data(ticker)
            df = features(df)
            df = create_labels(df)
            df.to_csv(BASE_DIR/f"data/price/{ticker}_price.csv")
            model, X_test = train_model(df)
            pred_data = predict(model, X_test, df)
            pred_data.to_csv(BASE_DIR/f"data/pred/{ticker}_pred.csv")
            joblib.dump(model, path)
            _model_cache[ticker] = model
        else:
            _model_cache[ticker] = joblib.load(path)
    return _model_cache[ticker]

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
