"use client";

import { useState, useCallback, useRef, useEffect } from "react";

const API_BASE = "http://localhost:8000";

export interface ScanResult {
    symbol: string;
    score: number;
    ltp: number;
    trend: string;
    setup_type: string;
    signals: string[];
    stopLoss: number;
    target1: number;
    target2: number;
    timestamp: string;
    indicators?: {
        rsi: number;
        ema20: number;
        ema50: number;
        ema_cross: string;
        volume_ratio: number;
        supertrend: string;
        vwap_position: string;
        trend_strength: string;
        support_dist: number;
    };
}

export interface ScanPreset {
    name: string;
    description: string;
    icon: string;
    conditions: { indicator: string; operator: string; value: number | string }[];
}

export interface UniverseInfo {
    count: number;
    stocks: string[];
}

export function useScannerData() {
    const [results, setResults] = useState<ScanResult[]>([]);
    const [presets, setPresets] = useState<Record<string, ScanPreset>>({});
    const [universes, setUniverses] = useState<Record<string, UniverseInfo>>({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [lastScanTime, setLastScanTime] = useState<string | null>(null);
    const [scanMeta, setScanMeta] = useState<{ universe: string; preset: string | null; count: number } | null>(null);
    const intervalRef = useRef<NodeJS.Timeout | null>(null);

    // Fetch available presets
    const fetchPresets = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/scan/presets`);
            if (res.ok) {
                const data = await res.json();
                if (data.presets) setPresets(data.presets);
                if (data.universes) setUniverses(data.universes);
            }
        } catch {
            // Presets will be empty, use fallback
        }
    }, []);

    // Run a live scan
    const runScan = useCallback(async (universe: string = "quick", preset?: string) => {
        setLoading(true);
        setError(null);
        try {
            let url = `${API_BASE}/scan/live?universe=${universe}`;
            if (preset) url += `&preset=${preset}`;

            const res = await fetch(url);
            if (!res.ok) throw new Error(`Scan failed: ${res.status}`);

            const data = await res.json();
            if (data.status === "error") throw new Error(data.error);

            setResults(data.data || []);
            setLastScanTime(data.timestamp);
            setScanMeta({
                universe: data.universe,
                preset: data.preset,
                count: data.count,
            });
        } catch (e: any) {
            setError(e.message);
            setResults([]);
        } finally {
            setLoading(false);
        }
    }, []);

    // Auto-refresh
    const startAutoRefresh = useCallback((universe: string, preset?: string, intervalMs: number = 60000) => {
        stopAutoRefresh();
        intervalRef.current = setInterval(() => {
            runScan(universe, preset);
        }, intervalMs);
    }, [runScan]);

    const stopAutoRefresh = useCallback(() => {
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }
    }, []);

    // Fetch presets on mount
    useEffect(() => {
        fetchPresets();
        return () => stopAutoRefresh();
    }, [fetchPresets, stopAutoRefresh]);

    return {
        results,
        presets,
        universes,
        loading,
        error,
        lastScanTime,
        scanMeta,
        runScan,
        startAutoRefresh,
        stopAutoRefresh,
    };
}
