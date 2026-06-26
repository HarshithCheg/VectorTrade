const BASE_URL = "http://127.0.0.1:8000";

function authHeaders() {
    const token = localStorage.getItem("access_token");
    return {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
    };
}

export interface LatestPriceResponse {
    ticker: string;
    price: number;
    date: string;
}

export async function getLatestPrice(ticker: string): Promise<LatestPriceResponse> {
    const response = await fetch(`${BASE_URL}/api/price/latest/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ ticker }),
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "Could not fetch latest price");
    }
    return data;
}

export interface TradeResponse {
    status: string;
    cash: string;
}

export async function buyShares(ticker: string, price: number, qty: number): Promise<TradeResponse> {
    const response = await fetch(`${BASE_URL}/api/trades/buy/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ ticker, price, qty }),
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "Buy order failed");
    }
    return data;
}

export async function sellShares(ticker: string, price: number, qty: number): Promise<TradeResponse> {
    const response = await fetch(`${BASE_URL}/api/trades/sell/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ ticker, price, qty }),
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "Sell order failed");
    }
    return data;
}
