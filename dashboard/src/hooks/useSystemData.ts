"use client";

import { useState, useEffect } from 'react';

// API Base URL - connects to FastAPI backend
const API_BASE = 'http://localhost:8000';

export function useSystemData() {
    const [marketStatus, setMarketStatus] = useState<any>(null);
    const [positions, setPositions] = useState<any[]>([]);
    const [latestScan, setLatestScan] = useState<any>(null);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            try {
                // Parallel fetching
                const [statusRes, posRes, scanRes] = await Promise.all([
                    fetch(`${API_BASE}/stats/market-pulse`).catch(() => null),
                    fetch(`${API_BASE}/positions`).catch(() => null),
                    fetch(`${API_BASE}/scan/latest`).catch(() => null)
                ]);

                if (statusRes && statusRes.ok) {
                    setMarketStatus(await statusRes.json());
                    setIsConnected(true);
                } else {
                    setIsConnected(false);
                }

                if (posRes && posRes.ok) {
                    const posData = await posRes.json();
                    setPositions(Array.isArray(posData) ? posData : (posData.positions || []));
                }
                if (scanRes && scanRes.ok) setLatestScan(await scanRes.json());

            } catch (error) {
                console.error("Failed to connect to Trading System:", error);
                setIsConnected(false);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 5000);

        return () => clearInterval(interval);
    }, []);

    return { marketStatus, positions, latestScan, isConnected };
}

export function useAccountData() {
    const [account, setAccount] = useState<any>(null);
    const [margins, setMargins] = useState<any>(null);
    const [holdings, setHoldings] = useState<any[]>([]);
    const [summary, setSummary] = useState<any>(null);

    useEffect(() => {
        const fetchAccount = async () => {
            try {
                const res = await fetch(`${API_BASE}/account/summary`).catch(() => null);
                if (res && res.ok) {
                    const data = await res.json();
                    setAccount(data.account || null);
                    setMargins(data.margins || null);
                    setHoldings(data.holdings || []);
                    setSummary(data);
                }
            } catch (error) {
                console.error("Failed to fetch account data:", error);
            }
        };

        fetchAccount();
        const interval = setInterval(fetchAccount, 10000);
        return () => clearInterval(interval);
    }, []);

    return { account, margins, holdings, summary };
}
