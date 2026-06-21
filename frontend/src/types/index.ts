export interface Portfolio{
    uid: string;
    owner: number;
    cash: string;
    created_at: string;
}

export interface Position{
    uid: string;
    portfolio: number;
    ticker: string;
    qty: string;
    avg_price: string;
}

export interface Trade{
    uid: string;
    portfolio: number;
    ticker: string;
    action: "BUY" | "SELL";
    qty: string;
    price: string;
    created_at: string;
}

export interface PredictResponse{
    ticker: string;
    date: string;
    signal: "BUY"|"SELL";
    confidence: number;
}

export interface AuthResponse{
    access: string;
    refresh: string;
    uid: string;
    username: string;
}