# VectorTrade

ML-powered algorithmic trading simulation platform. Combines a RandomForest-based price-direction classifier with a custom DSA-driven backtesting engine and a Django REST API, wrapped in a React + TypeScript dashboard.

VectorTrade does not give real trading advice or move real money. It is a learning/demo project that simulates trading decisions on real historical market data.

---

## Architecture

```
┌──────────────────────────────────────────────┐
│  PHASE 1 — ML BRAIN (src/brain.py)            │
│  Feature engineering + RandomForest classifier │
│  Outputs: BUY/SELL signal + confidence score   │
└───────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│  PHASE 2 — BACKTESTING ENGINE (src/engine.py)    │
│  Pure-Python DSA: dict-based positions (O(1)),   │
│  deque-based trade log, simulated P&L            │
└───────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│  PHASE 3 — DJANGO REST API (backend/)            │
│  JWT auth, Portfolio/Position/Trade models,      │
│  LP-based multi-ticker portfolio allocator        │
└───────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│  PHASE 4 — REACT + TYPESCRIPT FRONTEND           │
│  Dashboard: portfolio, positions, predict,       │
│  buy/sell, backtest, allocator, trade history    │
└──────────────────────────────────────────────────┘
```

---

## Features

- **Feature engineering** — momentum (1d/5d/10d returns), trend (SMA20/50 ratios), volatility, volume ratio, RSI-14
- **Chronologically safe train/test split** via `TimeSeriesSplit` — no lookahead bias
- **Model comparison** — RandomForest vs GradientBoosting vs LogisticRegression
- **Confidence-scored predictions** via `predict_proba`
- **Custom backtesting engine** built from scratch with hash maps and queues (no external backtesting library)
- **Linear Programming portfolio allocator** — uses `scipy.optimize.linprog` to rebalance across open positions toward higher-confidence signals, subject to a cash budget constraint
- **JWT-authenticated REST API** with auto-provisioned portfolios on signup (Django signals)
- **Auto-training pipeline** — requesting a prediction for a never-seen ticker trains and caches the model on the fly
- **React + TypeScript dashboard** — live predictions, manual trading, backtest runner, allocator runner, trade history

---

## Tech Stack

| Layer | Tech |
|---|---|
| ML | Python, pandas, scikit-learn, yfinance |
| Optimization | scipy.optimize (linprog) |
| Backend | Django, Django REST Framework, SimpleJWT |
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Storage | SQLite (dev) |

---

## Project Structure

```
VectorTrade/
├── src/
│   ├── brain.py          # ML pipeline: load data, engineer features, train model
│   ├── engine.py         # Backtesting engine: Engine class with buy/sell/backtest
│   └── utils.py          # Shared constants, model cache, predict(), calc_rsi()
├── backend/
│   ├── backend/          # Django project config (settings, urls)
│   └── trade/            # Main app: models, views, serializers, services
├── frontend/
│   └── src/
│       ├── api/          # fetch wrappers per domain (auth, portfolio, trade, backtest)
│       ├── pages/        # Login, Register, Dashboard
│       └── types/        # Shared TypeScript interfaces
├── data/
│   ├── price/            # Cached OHLCV CSVs per ticker
│   └── pred/              # Cached prediction CSVs per ticker
├── models/                # Serialized trained models (.pkl)
└── requirements.txt
```

---

## Setup

### Backend

```bash
cd VectorTrade
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

cd backend
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Backend runs at `http://127.0.0.1:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

### CORS

Make sure `django-cors-headers` is configured in `backend/settings.py` to allow `http://localhost:5173`, or the frontend won't be able to reach the API.

---

## API Reference

All endpoints except `register` and `login` require a JWT access token:
```
Authorization: Bearer <access_token>
```

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/register/` | Create account, returns JWT tokens immediately |
| POST | `/api/login/` | Authenticate, returns JWT tokens |
| POST | `/api/logout/` | Blacklist refresh token |
| GET | `/api/portfolio/` | Get current cash and portfolio info |
| GET | `/api/position/` | List open positions |
| GET | `/api/trades/log/` | List trade history |
| POST | `/api/trades/buy/` | Execute a buy order — `{ ticker, price, qty }` |
| POST | `/api/trades/sell/` | Execute a sell order — `{ ticker, price, qty }` |
| POST | `/api/price/latest/` | Get latest market close price for a ticker |
| POST | `/api/predict/` | Get BUY/SELL signal + confidence for a ticker — auto-trains if model doesn't exist |
| POST | `/api/backtest/` | Run historical backtest — `{ ticker, initial_cash }` |
| POST | `/api/portfolio/allocation` | Run LP-based portfolio rebalancing across all open positions |

A ticker that has never been trained on will trigger an automatic training run (downloads 5 years of OHLCV data, engineers features, trains RandomForest, caches the model) the first time it's requested via `/predict/` — this can take 30–60 seconds.

---

## ML Pipeline Details

**Label definition:** `1` if next day's close > today's close, else `0`.

**Features (9 total):**
- `returns_1d`, `returns_5d`, `returns_10d` — momentum at multiple timeframes
- `close_to_sma20`, `close_to_sma50` — price position relative to moving averages
- `volatility_10d` — rolling standard deviation of daily returns
- `volume_ratio` — today's volume vs 20-day average volume
- `hl_range` — intraday high-low range normalized by close
- `rsi_14` — Relative Strength Index

**Validation:** `TimeSeriesSplit(n_splits=5)`, evaluated on the final (most recent) fold to simulate real deployment conditions. Regular k-fold or shuffled train/test splits are intentionally avoided — they would leak future information into training.

**Model selection:** RandomForest, GradientBoosting, and LogisticRegression (with StandardScaler) are compared; RandomForest is used in production for its native handling of non-linear feature interactions without requiring feature scaling.

**Typical accuracy:** ~50–55%. This is expected and realistic for daily price-direction prediction — markets are close to efficient at this granularity, and even a few percentage points above chance is the basis of real quantitative trading edges when combined with proper risk management and execution.

---

## The DSA Backtesting Engine

`engine.py` is a hand-built simulator using only core Python data structures:

- **`dict`** — O(1) position lookups (`positions[ticker]`)
- **`deque`** — chronological trade log (`order_log`)
- Weighted-average cost basis tracking on every buy
- Guards against insufficient funds / insufficient shares

The engine replays a model's predictions against historical prices day-by-day, executing simulated buy/sell orders and reporting final portfolio value and P&L — entirely independent of any external backtesting library.

---

## Portfolio Allocator (Linear Programming)

`PortfolioAllocator` formulates capital allocation across multiple open positions as a linear program, solved with `scipy.optimize.linprog` (HiGHS solver — interior point + simplex hybrid):

```
maximize    Σ (confidence_i × qty_i)
subject to  Σ (price_i × qty_i) ≤ available_cash
            qty_i ≥ -current_holding_i   (can't sell more than held)
```

Sells are executed first (for positions where confidence < 50%) to free up capital, cash is refreshed from the database, and the LP then solves for buys only using the updated cash balance.

---

## Known Limitations

- **LP objective is share-count biased, not capital-weighted.** The current objective maximizes `confidence × quantity`, which favors low-priced stocks since more shares can be purchased per dollar. A more correct formulation would optimize `confidence × dollars_invested`, treating the decision variable as capital allocated rather than share count, then converting to shares after solving. Planned fix.

- **Single-currency assumption.** All price and cash calculations assume USD. International tickers (e.g. `RELIANCE.NS` on the NSE, priced in INR) are not currency-normalized. Mixing USD and non-USD tickers in the same portfolio will produce incorrect LP and backtest results. A live FX-rate conversion layer (e.g. via `yfinance`'s `INR=X` ticker) would need to sit between price retrieval and any cash-based calculation.

- **No magnitude prediction.** The classifier predicts direction only (up/down), not expected size of the move. A 90%-confident signal predicting a 1% move and a 67%-confident signal predicting a 20% move are currently treated identically by the optimizer. A regression model predicting expected return magnitude, combined with classifier confidence into a true expected-value score, would meaningfully improve allocation quality.

- **No sequence modeling.** RandomForest treats each day as an independent observation. An LSTM/GRU model that ingests a rolling window of recent days could capture temporal patterns the current feature set can't.

- **No scheduled retraining.** Models are trained once (on the first prediction request) and cached indefinitely. A production system would retrain nightly via a scheduled job (e.g. Celery + Redis) to incorporate new market data.

---

## Future Work

- Deep learning model (LSTM/GRU) as an alternative/ensemble to RandomForest
- Regression-based expected-magnitude model feeding into a true expected-value LP objective
- Multi-currency support via live FX normalization
- Walk-forward validation across multiple TimeSeriesSplit folds rather than the single final fold
- Sharpe ratio and max drawdown as proper risk-adjusted backtest metrics
- Scheduled model retraining via Celery + Redis

---

## Disclaimer

This project is for educational purposes only. It does not constitute financial advice, and nothing in this repository should be used to make real investment decisions. Historical backtest performance does not guarantee future results.

---

## References

Sources used while researching the reasoning behind each feature and design choice:

**`returns_1d` / `returns_5d` / `returns_10d` (momentum)**
Multiple lookback windows are used so the model can separate immediate, weekly, and bi-weekly momentum instead of blending them into one number.
- [Investopedia — Momentum Investing](https://www.investopedia.com/terms/m/momentum_investing.asp)
- [Investopedia — Price Rate of Change (ROC)](https://www.investopedia.com/terms/p/pricerateofchange.asp)

**`close_to_sma20` / `close_to_sma50` (trend)**
20-day and 50-day moving averages are two of the most commonly referenced indicators in retail and swing trading. Using the price-to-SMA *ratio* instead of the raw average keeps the feature comparable across stocks with very different price levels.
- [Investopedia — Simple Moving Average (SMA)](https://www.investopedia.com/terms/s/sma.asp)
- [Fidelity Learning Center — Moving averages](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/moving-average)

**`volatility_10d` (rolling standard deviation of returns)**
Volatility tends to cluster — calm stretches stay calm, choppy stretches stay choppy — which is why a rolling window rather than a single overall standard deviation is used.
- [Investopedia — Volatility](https://www.investopedia.com/terms/v/volatility.asp)
- [Corporate Finance Institute — Historical volatility](https://corporatefinanceinstitute.com/resources/data-science/historical-volatility/)

**`volume_ratio` (today's volume vs 20-day average)**
A price move on unusually high volume is generally treated as a stronger, more reliable signal than the same move on thin trading.
- [Investopedia — Volume Analysis](https://www.investopedia.com/articles/technical/02/010702.asp)
- [Investopedia — On-Balance Volume (OBV)](https://www.investopedia.com/terms/o/onbalancevolume.asp)

**`hl_range` (intraday high-low range / close)**
A simplified relative of Average True Range — wider intraday ranges relative to price suggest more indecision/pressure between buyers and sellers that day.
- [Investopedia — Average True Range (ATR)](https://www.investopedia.com/terms/a/atr.asp)

**`rsi_14` (Relative Strength Index)**
RSI scores recent price action on a 0–100 scale, with the conventional 70/30 overbought/oversold thresholds and the 14-day period both coming from the indicator's original design — still the standard default used everywhere it's implemented.
- [Investopedia — Relative Strength Index (RSI)](https://www.investopedia.com/terms/r/rsi.asp)
- [StockCharts ChartSchool — RSI](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi)

**`TimeSeriesSplit` instead of a random train/test split**
Shuffling time-ordered data lets the model train on the future to predict the past — looks great in testing, falls apart in production. This is a commonly flagged beginner mistake in ML-for-finance guides and is exactly what `TimeSeriesSplit` is built to prevent.
- [scikit-learn docs — TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html)
- [Towards Data Science — Time series cross-validation done right](https://towardsdatascience.com/time-series-nested-cross-validation-76adba623eb9)

**RandomForest as the production model**
Chosen over Logistic Regression and Gradient Boosting because it needs no feature scaling, handles non-linear feature interactions out of the box, and averaging many decorrelated trees (each trained on a random subset of rows *and* features) reduces overfitting compared to a single tree.
- [scikit-learn docs — RandomForestClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html)
- [Towards Data Science — Understanding Random Forest](https://towardsdatascience.com/understanding-random-forest-58381e0602d2)

**Linear Programming for portfolio allocation**
Capital allocation under a fixed cash budget is a classic constrained-optimization setup — maximize total confidence-weighted return subject to a spending limit — solved here with scipy's LP solver instead of writing a custom greedy heuristic.
- [scipy docs — linprog](https://docs.scipy.org/doc/scipy/reference/optimize.linprog-highs.html)
- [Investopedia — Modern Portfolio Theory (MPT)](https://www.investopedia.com/terms/m/modernportfoliotheory.asp) — the general idea this is a simplified linear take on

**Confidence thresholding via `predict_proba`**
Using the model's predicted probability instead of just its 0/1 output lets trades be sized or filtered by how confident the model actually is, rather than treating every signal as equally strong.
- [scikit-learn docs — predict_proba](https://scikit-learn.org/stable/glossary.html#term-predict_proba)
- [Investopedia — Kelly Criterion](https://www.investopedia.com/articles/trading/04/091504.asp) — the general principle behind sizing bets by confidence rather than treating every bet the same
