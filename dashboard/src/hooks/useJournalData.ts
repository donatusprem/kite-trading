"use client";

import { useState, useEffect, useCallback } from "react";

const API_BASE = "http://localhost:8000";

export interface Trade {
    trade_id: string;
    symbol: string;
    status: string;
    entry_price: number;
    exit_price?: number;
    quantity: number;
    position_size: number;
    pnl: number;
    pnl_pct: number;
    r_multiple: number;
    hold_time_minutes: number;
    entry_time: string;
    exit_time?: string;
    exit_type?: string;
    exit_reason?: string;
    entry_reason?: string;
    score: number;
    setup_type?: string;
}

export interface PerformanceSummary {
    total_trades: number;
    wins: number;
    losses: number;
    win_rate: number;
    total_pnl: number;
    avg_pnl_per_trade: number;
    avg_r_multiple: number;
    avg_hold_time_minutes: number;
    exit_types: Record<string, number>;
    error?: string;
}

export interface DayActivity {
    scans: number;
    trades: number;
    entries: any[];
}

export function useJournalData() {
    const [trades, setTrades] = useState<Trade[]>([]);
    const [summary, setSummary] = useState<PerformanceSummary | null>(null);
    const [activity, setActivity] = useState<Record<string, DayActivity>>({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchJournal = useCallback(async () => {
        setLoading(true);
        try {
            const [tradesRes, activityRes] = await Promise.all([
                fetch(`${API_BASE}/journal/trades`).catch(() => null),
                fetch(`${API_BASE}/journal/activity`).catch(() => null),
            ]);

            if (tradesRes && tradesRes.ok) {
                const data = await tradesRes.json();
                setTrades(data.trades || []);
                setSummary(data.summary || null);
            }

            if (activityRes && activityRes.ok) {
                const data = await activityRes.json();
                setActivity(data.activity || {});
            }

            setError(null);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchJournal();
        const interval = setInterval(fetchJournal, 30000);
        return () => clearInterval(interval);
    }, [fetchJournal]);

    return { trades, summary, activity, loading, error, refresh: fetchJournal };
}
