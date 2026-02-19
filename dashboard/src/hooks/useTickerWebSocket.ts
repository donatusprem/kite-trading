"use client";

import { useState, useEffect, useRef, useCallback } from 'react';

const WS_URL = 'ws://localhost:8000/ws/ticks';
const API_BASE = 'http://localhost:8000';

interface TickData {
    ltp: number;
    volume: number;
    change: number;
    open: number;
    high: number;
    low: number;
    close: number;
    oi: number;
    updated_at: string;
}

interface TickerState {
    ticks: Record<string, TickData>;
    isConnected: boolean;
    isLive: boolean;
    lastUpdate: string | null;
    instrumentCount: number;
}

/**
 * useTickerWebSocket — Real-time tick streaming via WebSocket.
 * 
 * Connects to the backend's /ws/ticks endpoint and receives
 * tick-by-tick price updates. Falls back to REST polling if
 * the WebSocket connection fails.
 */
export function useTickerWebSocket(): TickerState & {
    getPrice: (symbol: string) => TickData | null;
    reconnect: () => void;
} {
    const [ticks, setTicks] = useState<Record<string, TickData>>({});
    const [isConnected, setIsConnected] = useState(false);
    const [isLive, setIsLive] = useState(false);
    const [lastUpdate, setLastUpdate] = useState<string | null>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const fallbackIntervalRef = useRef<NodeJS.Timeout | null>(null);

    const connect = useCallback(() => {
        // Clean up existing connection
        if (wsRef.current) {
            wsRef.current.close();
        }

        try {
            const ws = new WebSocket(WS_URL);
            wsRef.current = ws;

            ws.onopen = () => {
                console.log('[Ticker] WebSocket connected');
                setIsConnected(true);
                setIsLive(true);
                // Clear fallback polling since WS is active
                if (fallbackIntervalRef.current) {
                    clearInterval(fallbackIntervalRef.current);
                    fallbackIntervalRef.current = null;
                }
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.ticks) {
                        setTicks(data.ticks);
                        setLastUpdate(data.timestamp);
                        setIsLive(true);
                    }
                } catch (e) {
                    console.error('[Ticker] Parse error:', e);
                }
            };

            ws.onclose = (event) => {
                console.log('[Ticker] WebSocket closed:', event.code);
                setIsConnected(false);
                setIsLive(false);

                // Auto-reconnect after 3 seconds
                reconnectTimeoutRef.current = setTimeout(() => {
                    console.log('[Ticker] Attempting reconnect...');
                    connect();
                }, 3000);

                // Start fallback REST polling
                startFallbackPolling();
            };

            ws.onerror = () => {
                // Suppress noisy errors — backend may not be running yet.
                // Auto-reconnect in onclose will handle recovery.
                setIsConnected(false);
            };
        } catch (e) {
            console.error('[Ticker] Connection failed:', e);
            setIsConnected(false);
            startFallbackPolling();
        }
    }, []);

    const startFallbackPolling = useCallback(() => {
        if (fallbackIntervalRef.current) return; // Already polling

        console.log('[Ticker] Starting REST fallback polling');
        fallbackIntervalRef.current = setInterval(async () => {
            try {
                const res = await fetch(`${API_BASE}/ticks/latest`);
                if (res.ok) {
                    const data = await res.json();
                    if (data.ticks) {
                        setTicks(data.ticks);
                        setLastUpdate(data.timestamp);
                    }
                }
            } catch {
                // Silently fail — WS reconnect will take over
            }
        }, 2000);
    }, []);

    const reconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }
        connect();
    }, [connect]);

    const getPrice = useCallback((symbol: string): TickData | null => {
        return ticks[symbol] || null;
    }, [ticks]);

    // Connect on mount
    useEffect(() => {
        connect();

        return () => {
            if (wsRef.current) wsRef.current.close();
            if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
            if (fallbackIntervalRef.current) clearInterval(fallbackIntervalRef.current);
        };
    }, [connect]);

    return {
        ticks,
        isConnected,
        isLive,
        lastUpdate,
        instrumentCount: Object.keys(ticks).length,
        getPrice,
        reconnect
    };
}
