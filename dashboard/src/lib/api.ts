const API_BASE = "http://localhost:8000";

export async function fetchApi<T>(endpoint: string): Promise<T | null> {
    try {
        const res = await fetch(`${API_BASE}${endpoint}`);
        if (!res.ok) return null;
        return await res.json();
    } catch {
        return null;
    }
}

export async function postApi<T>(endpoint: string, body?: any): Promise<T | null> {
    try {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: body ? JSON.stringify(body) : undefined,
        });
        if (!res.ok) return null;
        return await res.json();
    } catch {
        return null;
    }
}

// Types
export interface SignalAnalysis {
    direction: string;
    confidence: number;
    trend_strength: string;
    vwap: { value: number; position: string; deviation_pct: number };
    rsi: { value: number; zone: string; divergence: { type: string } };
    supertrend: { signal: string; value: number };
    ema: { trend: string; aligned: boolean };
    atr: { value: number; pct: number };
    volume: { ratio: number; surge: boolean };
    signals: string[];
    scores: { bull: number; bear: number };
}

export interface RiskDashboard {
    portfolio_heat: { current_pct: number; status: string; remaining_budget: number };
    drawdown: { status: string; daily_pct: number; weekly_pct: number };
    open_positions: number;
    max_positions: number;
}

export interface TradeRecommendation {
    symbol: string;
    score: number;
    setup_type: string;
    signal: {
        direction: string;
        confidence: number;
        trend_strength: string;
        signals: string[];
    };
    mode: { mode: string; reason: string; product: string; expiry_preference?: string };
    risk: { status: string; reasons?: string[] };
    price: number;
    error?: string;
}

export interface ModuleStatus {
    modules: Record<string, string>;
    timestamp: string;
}
