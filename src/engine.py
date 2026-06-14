from collections import deque
import heapq
from datetime import date
import joblib
from utils import TICKER
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Engine:
    def __init__(self, initCash):
        self.initialCash = initCash
        self.cash = initCash
        self.positions = {}
        self.order_log = deque()
        self.buy_heap = []

    def status(self):
        print(f"Cash: {self.cash}")
        print(f"Open Positions: {self.positions}")
        print(f"Total Trades: {len(self.order_log)}")
    
    def buy(self, ticker, price, qty):
        cost = price*qty
        if cost > self.cash:
            raise ValueError("Insufficient Funds")
        
        if ticker in self.positions:
            self.positions[ticker][1] = (self.positions[ticker][1]*self.positions[ticker][0] + price*qty)/(qty + self.positions[ticker][0])
            self.positions[ticker][0] += qty
        else:
            self.positions[ticker] = [qty, price]
        self.cash -= cost

        self.order_log.append((date.today(), ticker, "BUY", qty, price))
    
    def sell(self, ticker, price, qty):
        if ticker not in self.positions:
            raise KeyError("No Shares")
        if qty > self.positions[ticker][0]:
            raise ValueError("Insufficient Shares")
        income = price*qty

        self.positions[ticker][0] -= qty
        if self.positions[ticker][0] == 0:
            self.positions.pop(ticker, None)
        self.cash += income

        self.order_log.append((date.today(), ticker, "SELL", qty, price))

    def portfolio_value(self, market_price):
        value = self.cash
        for name, data in self.positions.items():
            value += data[0]*market_price[name]
        return value

    def profit_loss(self, market_price):
        return self.portfolio_value(market_price) - self.initialCash
    
    def addCash(self, amount):
        self.cash += amount
    
    def debitCash(self, amount):
        self.cash -= amount

    def run_backtest(self, pred_df, price_df, ticker, qty = 10):
        price_df["Date"] = pd.to_datetime(price_df["Date"])
        pred_df["Date"] = pd.to_datetime(pred_df["Date"])
        merged = pd.merge(price_df, pred_df, how="inner", on="Date")

        for row in merged.itertuples():
            if row.Predicted == 1:
                try:
                    self.buy(ticker, row.Close, qty)
                except ValueError:
                    pass
            elif row.Predicted == 0:
                try:
                    self.sell(ticker, row.Close, qty)
                except (ValueError, KeyError):
                    pass

        last_price = {ticker: merged["Close"].iloc[-1]}
        return {"Portfolio Value": self.portfolio_value(last_price),
                "Profit/Loss": self.profit_loss(last_price)}
        

if __name__ == "__main__":
    #model = joblib.load(f"../models/{TICKER}_model.pkl") ran into some windows path issue
    #above type path should work well for Linux/MAC
    model = joblib.load(BASE_DIR/f"models/{TICKER}_model.pkl")
    pred_df = pd.read_csv(BASE_DIR/f"data/pred/{TICKER}_pred.csv")
    price_df = pd.read_csv(BASE_DIR/f"data/price/{TICKER}_price.csv")

    engine = Engine(100000)
    print(engine.run_backtest(pred_df, price_df, TICKER))
