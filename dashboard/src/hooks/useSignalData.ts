"use client";

import { useState, useCallback } from "react";
import { fetchApi, type SignalAnalysis, type TradeRecommendation } from "@/lib/api";

export function useSignalData() {
    const [signal, setSignal] = useState<SignalAnalysis | null>(null);
    const [recommendation, setRecommendation] = useState<TradeRecommendation | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const analyzeSymbol = useCallback(async (symbol: string) => {
        setLoading(true);
        setError(null);
        try {
            const data = await fetchApi<{ symbol: string; analysis: SignalAnalysis }>(
                `/signal/${symbol}`
            );
            if (data?.analysis) {
                setSignal(data.analysis);
            } else {
                setError("No signal data available");
            }
        } catch (e: any) {
            setError(e.message || "Failed to analyze");
        } finally {
            setLoading(false);
        }
    }, []);

    const getRecommendation = useCallback(async (symbol: string) => {
        setLoading(true);
        setError(null);
        try {
            const data = await fetchApi<TradeRecommendation>(`/trade/recommend/${symbol}`);
            if (data && !data.error) {
                setRecommendation(data);
            } else {
                setError(data?.error || "No recommendation available");
            }
        } catch (e: any) {
            setError(e.message || "Failed to get recommendation");
        } finally {
            setLoading(false);
        }
    }, []);

    return { signal, recommendation, loading, error, analyzeSymbol, getRecommendation };
}
