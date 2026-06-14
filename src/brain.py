import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble import RandomForestClassifier

#to avoid cycle imports removed "from utils import ..."

FEATURE = ["returns_1d", "returns_5d", "returns_10d", "close_to_sma20", "close_to_sma50", "volatility_10d", "volume_ratio", "hl_range", "rsi_14"]
def load_data(ticker, period = '5y'):
    data = yf.download(ticker, period=period, auto_adjust=True)
    data.columns.names = [None, None]
    data.columns = data.columns.get_level_values(0)
    data.reset_index(inplace=True)
    data = data.dropna()
    return data

def calc_rsi(close, period=14): #exists in utils also
    change = close.diff()
    gain = change.clip(lower=0).rolling(period).mean() 
    loss = (-change.clip(upper=0)).rolling(period).mean() 
    rs = gain/loss.replace(0, 1e-10)
    return 100 - (100/(1+rs))

#creates multiple features
def features(df):
    #we use multiple periods/time-frames to get a holistic picture of the stock.
    #short term momentum
    df["returns_1d"] = df["Close"].pct_change(1)
    df["returns_5d"] = df["Close"].pct_change(5)
    df["returns_10d"] = df["Close"].pct_change(10)

    #moving avg to show actual trend and ignore noises
    df["sma_20"] = df["Close"].rolling(20).mean()
    df["sma_50"] = df["Close"].rolling(50).mean()

    #is the stock undervalued or overvalued
    df["close_to_sma20"] = df["Close"]/df["sma_20"]
    df["close_to_sma50"] = df["Close"]/df["sma_50"]

    #turbulent the share has been
    df["volatility_10d"] = df["returns_1d"].rolling(10).std()

    #volume ratio: determine if spike/drop is in relation to volume
    df["volume_ratio"] = df["Volume"] / df["Volume"].rolling(20).mean()

    #per day candle
    df["hl_range"] = (df["High"] - df["Low"])/ df["Close"]

    #add rsi - very imp feature
    df["rsi_14"] = calc_rsi(df["Close"])
    df = df.dropna()
    return df

#Main label 1-> buy | 0-> sell
def create_labels(df):
    df["target"] = np.where(df["Close"] < df["Close"].shift(-1), 1, 0)
    df.dropna(inplace=True)
    return df

#Modified Data Split using TimeSeriesSplit
def split_data(df):    
    X = df[FEATURE]
    y = df["target"]

    #test_train_split can be use if shuffle=False but wont help you know how much past 
    # is good enough to analyse (gives only 1 window).
    #use time_series_split to maintain the chronological order(row 0 came before row 1)
    time = TimeSeriesSplit(n_splits=5) # generally used but can be anything (5 windows)
    splits = list(time.split(X, y))
    train_idx, test_idx = splits[-1]

    X_train = X.iloc[train_idx]
    y_train = y.iloc[train_idx]
    X_test = X.iloc[test_idx]
    y_test = y.iloc[test_idx]

    #safety check 
    X_train = X_train.replace([np.inf, -np.inf], np.nan).dropna()
    y_train = y_train[X_train.index]
    X_test = X_test.replace([np.inf, -np.inf], np.nan).dropna()
    y_test = y_test[X_test.index]
    return X_train, X_test, y_train, y_test

        
#chose RandomForest
def train_model(df):
    X_train, X_test, y_train, y_test = split_data(df)
    rfc = RandomForestClassifier(n_estimators=100, random_state=42)
    rfc.fit(X_train, y_train)
    return rfc, X_test
