import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { Portfolio, Position, Trade } from "../types";
import { getPortfolio, getPositions } from "../api/portfolio";
import { predictTicker } from "../api/trade";
import { buyShares, sellShares, getLatestPrice } from "../api/trade_actions";
import { runBacktest, runAllocation } from "../api/backtest";
import type { BacktestResult, AllocationResult } from "../api/backtest";
import { getTradeLog, logoutUser } from "../api/log";

const inputClass =
    "flex-1 bg-[#0A0A0F] border border-[#232330] rounded-md px-3 py-2 text-sm font-mono placeholder:text-[#3F3F4D] focus:outline-none focus:border-[#00E08C]";
const btnClass =
    "bg-[#00E08C] text-[#04342C] font-medium text-sm px-4 py-2 rounded-md hover:bg-[#00C97D] transition-colors disabled:opacity-50 whitespace-nowrap";
const cardClass = "bg-[#13131A] border border-[#232330] rounded-lg p-5";
const labelClass = "text-white text-sm font-medium mb-4";

export default function Dashboard() {
    const navigate = useNavigate();

    const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
    const [positions, setPositions] = useState<Position[]>([]);
    const [trades, setTrades] = useState<Trade[]>([]);

    const [ticker, setTicker] = useState("");
    const [signal, setSignal] = useState<{ signal: string; confidence: number } | null>(null);
    const [loadingSignal, setLoadingSignal] = useState(false);

    const [tradeTicker, setTradeTicker] = useState("");
    const [tradePrice, setTradePrice] = useState<number | null>(null);
    const [tradeQty, setTradeQty] = useState("");
    const [loadingTrade, setLoadingTrade] = useState(false);
    const [loadingPrice, setLoadingPrice] = useState(false);

    const [backtestTicker, setBacktestTicker] = useState("");
    const [backtestCash, setBacktestCash] = useState("100000");
    const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
    const [loadingBacktest, setLoadingBacktest] = useState(false);

    const [allocResult, setAllocResult] = useState<AllocationResult | null>(null);
    const [loadingAlloc, setLoadingAlloc] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem("access_token");
        if (!token) {
            navigate("/login");
            return;
        }
        loadData();
    }, []);

    async function loadData() {
        try {
            const p = await getPortfolio();
            setPortfolio(p);
            const pos = await getPositions();
            setPositions(pos);
            const log = await getTradeLog();
            setTrades(log);
        } catch (err) {
            navigate("/login");
        }
    }

    async function handlePredict(e: React.SyntheticEvent) {
        e.preventDefault();
        if (!ticker) return;
        setLoadingSignal(true);
        setSignal(null);
        try {
            const result = await predictTicker(ticker.toUpperCase());
            setSignal({ signal: result.signal, confidence: result.confidence });
        } catch (err) {
            alert("Could not fetch prediction — check the ticker symbol");
        } finally {
            setLoadingSignal(false);
        }
    }

    async function handleFetchPrice() {
        if (!tradeTicker) return;
        setLoadingPrice(true);
        setTradePrice(null);
        try {
            const result = await getLatestPrice(tradeTicker.toUpperCase());
            setTradePrice(result.price);
        } catch (err) {
            alert("Could not fetch price — check the ticker symbol");
        } finally {
            setLoadingPrice(false);
        }
    }

    async function handleBuy(e: React.SyntheticEvent) {
        e.preventDefault();
        if (!tradeTicker || tradePrice === null || !tradeQty) return;
        setLoadingTrade(true);
        try {
            await buyShares(tradeTicker.toUpperCase(), tradePrice, Number(tradeQty));
            await loadData();
            setTradeTicker("");
            setTradePrice(null);
            setTradeQty("");
        } catch (err) {
            alert(err instanceof Error ? err.message : "Buy failed");
        } finally {
            setLoadingTrade(false);
        }
    }

    async function handleSell(e: React.SyntheticEvent) {
        e.preventDefault();
        if (!tradeTicker || tradePrice === null || !tradeQty) return;
        setLoadingTrade(true);
        try {
            await sellShares(tradeTicker.toUpperCase(), tradePrice, Number(tradeQty));
            await loadData();
            setTradeTicker("");
            setTradePrice(null);
            setTradeQty("");
        } catch (err) {
            alert(err instanceof Error ? err.message : "Sell failed");
        } finally {
            setLoadingTrade(false);
        }
    }

    async function handleBacktest(e: React.SyntheticEvent) {
        e.preventDefault();
        if (!backtestTicker) return;
        setLoadingBacktest(true);
        setBacktestResult(null);
        try {
            const result = await runBacktest(backtestTicker.toUpperCase(), Number(backtestCash));
            setBacktestResult(result);
        } catch (err) {
            alert("Backtest failed — check the ticker symbol");
        } finally {
            setLoadingBacktest(false);
        }
    }

    async function handleAllocate() {
        setLoadingAlloc(true);
        setAllocResult(null);
        try {
            const result = await runAllocation();
            setAllocResult(result);
            await loadData();
        } catch (err) {
            alert(err instanceof Error ? err.message : "Allocation failed");
        } finally {
            setLoadingAlloc(false);
        }
    }

    async function logout() {
        try {
            await logoutUser();
        } catch (err) {
            // clear session locally even if backend call fails
        }
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        navigate("/login");
    }

    const cash = portfolio ? Number(portfolio.cash) : 0;
    const positionsValue = positions.reduce(
        (sum, p) => sum + Number(p.qty) * Number(p.avg_price),
        0
    );
    const totalValue = cash + positionsValue;

    return (
        <div className="min-h-screen bg-[#0A0A0F] text-white">
            <div className="border-b border-[#232330] px-6 py-4 flex items-center justify-between">
                <div className="font-mono text-[#00E08C] text-xs tracking-[0.3em]">VECTORTRADE</div>
                <button onClick={logout} className="text-[#6B6B7D] text-sm hover:text-white transition-colors">
                    Sign out
                </button>
            </div>

            <div className="max-w-6xl mx-auto px-6 py-10">

                <div className="grid grid-cols-3 gap-4 mb-8">
                    <div className={cardClass}>
                        <div className="text-[#6B6B7D] text-xs font-mono tracking-wide mb-2">TOTAL VALUE</div>
                        <div className="font-mono text-2xl font-medium">
                            ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </div>
                    </div>
                    <div className={cardClass}>
                        <div className="text-[#6B6B7D] text-xs font-mono tracking-wide mb-2">CASH</div>
                        <div className="font-mono text-2xl font-medium">
                            ${cash.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </div>
                    </div>
                    <div className={cardClass}>
                        <div className="text-[#6B6B7D] text-xs font-mono tracking-wide mb-2">OPEN POSITIONS</div>
                        <div className="font-mono text-2xl font-medium">{positions.length}</div>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-6 mb-6">

                    <div className={cardClass}>
                        <div className={labelClass}>Positions</div>
                        {positions.length === 0 ? (
                            <p className="text-[#6B6B7D] text-sm">No open positions yet.</p>
                        ) : (
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="text-[#6B6B7D] text-xs font-mono border-b border-[#232330]">
                                        <th className="text-left pb-2">TICKER</th>
                                        <th className="text-right pb-2">QTY</th>
                                        <th className="text-right pb-2">AVG PRICE</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {positions.map((p) => (
                                        <tr key={p.uid} className="border-b border-[#1A1A22] last:border-0">
                                            <td className="py-2.5 font-mono text-[#00E08C]">{p.ticker}</td>
                                            <td className="py-2.5 text-right font-mono">{Number(p.qty).toFixed(2)}</td>
                                            <td className="py-2.5 text-right font-mono">${Number(p.avg_price).toFixed(2)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>

                    <div className={cardClass}>
                        <div className={labelClass}>Get a signal</div>
                        <form onSubmit={handlePredict} className="flex gap-2 mb-4">
                            <input
                                type="text"
                                value={ticker}
                                onChange={(e) => setTicker(e.target.value)}
                                placeholder="AAPL"
                                className={inputClass}
                            />
                            <button type="submit" disabled={loadingSignal} className={btnClass}>
                                {loadingSignal ? "..." : "Predict"}
                            </button>
                        </form>
                        {signal && (
                            <div className="border-t border-[#232330] pt-4">
                                <div className="flex items-baseline justify-between">
                                    <span
                                        className={`font-mono text-xl font-semibold ${
                                            signal.signal === "BUY" ? "text-[#00E08C]" : "text-[#FF4D6A]"
                                        }`}
                                    >
                                        {signal.signal}
                                    </span>
                                    <span className="text-[#6B6B7D] text-sm font-mono">
                                        {(signal.confidence * 100).toFixed(1)}% confidence
                                    </span>
                                </div>
                            </div>
                        )}
                        {loadingSignal && (
                            <p className="text-[#6B6B7D] text-xs mt-2">
                                Training model if needed — this can take a minute the first time.
                            </p>
                        )}
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-6 mb-6">

                    <div className={cardClass}>
                        <div className={labelClass}>Place an order</div>
                        <div className="space-y-2 mb-4">
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={tradeTicker}
                                    onChange={(e) => {
                                        setTradeTicker(e.target.value);
                                        setTradePrice(null);
                                    }}
                                    placeholder="Ticker (AAPL)"
                                    className={inputClass}
                                />
                                <button
                                    onClick={handleFetchPrice}
                                    disabled={loadingPrice || !tradeTicker}
                                    className={btnClass}
                                >
                                    {loadingPrice ? "..." : "Get price"}
                                </button>
                            </div>

                            {tradePrice !== null && (
                                <div className="flex items-baseline justify-between bg-[#0A0A0F] border border-[#232330] rounded-md px-3 py-2">
                                    <span className="text-[#6B6B7D] text-xs font-mono">MARKET PRICE</span>
                                    <span className="font-mono text-sm text-[#00E08C]">${tradePrice.toFixed(2)}</span>
                                </div>
                            )}

                            <input
                                type="number"
                                value={tradeQty}
                                onChange={(e) => setTradeQty(e.target.value)}
                                placeholder="Quantity"
                                step="0.0001"
                                className={`${inputClass} w-full`}
                            />
                        </div>
                        <div className="flex gap-2">
                            <button
                                onClick={handleBuy}
                                disabled={loadingTrade || tradePrice === null}
                                className="flex-1 bg-[#00E08C] text-[#04342C] font-medium text-sm py-2 rounded-md hover:bg-[#00C97D] transition-colors disabled:opacity-50"
                            >
                                Buy
                            </button>
                            <button
                                onClick={handleSell}
                                disabled={loadingTrade || tradePrice === null}
                                className="flex-1 bg-[#FF4D6A] text-[#4A1018] font-medium text-sm py-2 rounded-md hover:bg-[#E63E59] transition-colors disabled:opacity-50"
                            >
                                Sell
                            </button>
                        </div>
                    </div>

                    <div className={cardClass}>
                        <div className={labelClass}>Backtest a strategy</div>
                        <form onSubmit={handleBacktest} className="space-y-2 mb-4">
                            <input
                                type="text"
                                value={backtestTicker}
                                onChange={(e) => setBacktestTicker(e.target.value)}
                                placeholder="Ticker (AAPL)"
                                className={`${inputClass} w-full`}
                            />
                            <div className="flex gap-2">
                                <input
                                    type="number"
                                    value={backtestCash}
                                    onChange={(e) => setBacktestCash(e.target.value)}
                                    placeholder="Starting cash"
                                    className={inputClass}
                                />
                                <button type="submit" disabled={loadingBacktest} className={btnClass}>
                                    {loadingBacktest ? "Running..." : "Run"}
                                </button>
                            </div>
                        </form>
                        {backtestResult && (
                            <div className="border-t border-[#232330] pt-4 flex items-baseline justify-between">
                                <span className="font-mono text-lg">
                                    ${backtestResult["Portfolio Value"].toLocaleString(undefined, { maximumFractionDigits: 2 })}
                                </span>
                                <span
                                    className={`font-mono text-sm font-medium ${
                                        backtestResult["Profit/Loss"] >= 0 ? "text-[#00E08C]" : "text-[#FF4D6A]"
                                    }`}
                                >
                                    {backtestResult["Profit/Loss"] >= 0 ? "+" : ""}
                                    ${backtestResult["Profit/Loss"].toLocaleString(undefined, { maximumFractionDigits: 2 })}
                                </span>
                            </div>
                        )}
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-6 mb-6">

                    <div className={cardClass}>
                        <div className={labelClass}>Optimize allocation</div>
                        <p className="text-[#6B6B7D] text-xs mb-4">
                            Runs linear programming across your open positions to rebalance toward higher-confidence signals.
                        </p>
                        <button
                            onClick={handleAllocate}
                            disabled={loadingAlloc || positions.length === 0}
                            className={`${btnClass} w-full mb-3`}
                        >
                            {loadingAlloc ? "Optimizing..." : "Run optimizer"}
                        </button>
                        {allocResult && (
                            <div className="border-t border-[#232330] pt-3 text-sm space-y-1">
                                {allocResult.trades_successful.map((t, i) => (
                                    <div key={i} className="flex justify-between font-mono text-xs">
                                        <span className={t.action === "BUY" ? "text-[#00E08C]" : "text-[#FF4D6A]"}>
                                            {t.action} {t.ticker}
                                        </span>
                                        <span className="text-[#6B6B7D]">{t.qty}</span>
                                    </div>
                                ))}
                                {allocResult.trades_successful.length === 0 && (
                                    <p className="text-[#6B6B7D] text-xs">No rebalancing trades were needed.</p>
                                )}
                            </div>
                        )}
                    </div>

                    <div className={cardClass}>
                        <div className={labelClass}>Trade history</div>
                        {trades.length === 0 ? (
                            <p className="text-[#6B6B7D] text-sm">No trades yet.</p>
                        ) : (
                            <div className="max-h-48 overflow-y-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="text-[#6B6B7D] text-xs font-mono border-b border-[#232330]">
                                            <th className="text-left pb-2">TICKER</th>
                                            <th className="text-left pb-2">ACTION</th>
                                            <th className="text-right pb-2">QTY</th>
                                            <th className="text-right pb-2">PRICE</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {trades.slice(0, 10).map((t) => (
                                            <tr key={t.uid} className="border-b border-[#1A1A22] last:border-0">
                                                <td className="py-2 font-mono">{t.ticker}</td>
                                                <td className={`py-2 font-mono text-xs ${t.action === "BUY" ? "text-[#00E08C]" : "text-[#FF4D6A]"}`}>
                                                    {t.action}
                                                </td>
                                                <td className="py-2 text-right font-mono">{Number(t.qty).toFixed(2)}</td>
                                                <td className="py-2 text-right font-mono">${Number(t.price).toFixed(2)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
