import type { PredictResponse } from "../types";

const BASE_URL = "http://127.0.0.1:8000";

function authHeaders() {
    const token = localStorage.getItem("access_token");
    return {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
    };
}

export async function predictTicker(ticker: string): Promise<PredictResponse> {
    const response = await fetch(`${BASE_URL}/api/predict/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ ticker }),
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "Prediction failed");
    }
    return data;
}
