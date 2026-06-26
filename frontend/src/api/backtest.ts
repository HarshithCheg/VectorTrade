const BASE_URL = "http://127.0.0.1:8000";

function authHeaders() {
    const token = localStorage.getItem("access_token");
    return {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
    };
}

export interface BacktestResult {
    "Portfolio Value": number;
    "Profit/Loss": number;
}

export async function runBacktest(ticker: string, initialCash: number): Promise<BacktestResult> {
    const response = await fetch(`${BASE_URL}/api/backtest/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ ticker, initial_cash: initialCash }),
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "Backtest failed");
    }
    return data;
}

export interface AllocationResult {
    status: string;
    trades_successful: { ticker: string; action: string; qty: number }[];
    trades_failed: { ticker: string; action: string; error: string }[];
    remaining_cash: string;
}

export async function runAllocation(): Promise<AllocationResult> {
    const response = await fetch(`${BASE_URL}/api/portfolio/allocation`, {
        method: "POST",
        headers: authHeaders(),
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "Allocation failed");
    }
    return data;
}
