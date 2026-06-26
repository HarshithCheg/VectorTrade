import type { Portfolio, Position } from "../types";

const BASE_URL = "http://127.0.0.1:8000";

function authHeaders() {
    const token = localStorage.getItem("access_token");
    return {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
    };
}

export async function getPortfolio(): Promise<Portfolio> {
    const response = await fetch(`${BASE_URL}/api/portfolio/`, {
        method: "GET",
        headers: authHeaders(),
    });
    if (!response.ok) {
        throw new Error("Failed to fetch portfolio");
    }
    return response.json();
}

export async function getPositions(): Promise<Position[]> {
    const response = await fetch(`${BASE_URL}/api/position/`, {
        method: "GET",
        headers: authHeaders(),
    });
    if (!response.ok) {
        throw new Error("Failed to fetch positions");
    }
    return response.json();
}
