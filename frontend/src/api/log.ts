import type { Trade } from "../types";

const BASE_URL = "http://127.0.0.1:8000";

function authHeaders() {
    const token = localStorage.getItem("access_token");
    return {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
    };
}

export async function getTradeLog(): Promise<Trade[]> {
    const response = await fetch(`${BASE_URL}/api/trades/log/`, {
        method: "GET",
        headers: authHeaders(),
    });
    if (!response.ok) {
        throw new Error("Failed to fetch trade history");
    }
    return response.json();
}

export async function logoutUser(): Promise<void> {
    const refresh = localStorage.getItem("refresh_token");
    const response = await fetch(`${BASE_URL}/api/logout/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ refresh }),
    });
    if (!response.ok) {
        throw new Error("Logout failed");
    }
}
