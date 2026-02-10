"use client";

import { useState } from "react";
import { Search, Loader2, BarChart3, Zap } from "lucide-react";
import { cn } from "@/lib/utils";
import { useSignalData } from "@/hooks/useSignalData";
import { useRiskData } from "@/hooks/useRiskData";
import { SignalPanel } from "@/components/SignalPanel";
import { TradeRecommendation } from "@/components/TradeRecommendation";
import { RiskDashboardPanel } from "@/components/RiskDashboard";

const QUICK_SYMBOLS = ["RELIANCE", "HDFCBANK", "TCS", "INFY", "SBIN", "ITC", "ICICIBANK", "ADANIPORTS"];

export default function SignalsPage() {
    const [symbol, setSymbol] = useState("");
    const [activeSymbol, setActiveSymbol] = useState<string | null>(null);
    const { signal, recommendation, loading, error, analyzeSymbol, getRecommendation } = useSignalData();
    const { risk, modules } = useRiskData();

    const handleAnalyze = async (sym: string) => {
        const s = sym.toUpperCase().trim();
        if (!s) return;
        setActiveSymbol(s);
        await Promise.all([analyzeSymbol(s), getRecommendation(s)]);
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-white">Signal Engine</h1>
                    <p className="text-sm text-gray-400 mt-1">VWAP • RSI • Supertrend • Volume Profile • Multi-TF Confluence</p>
                </div>
                <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-primary" />
                    <span className="text-xs text-gray-400">Powered by yfinance</span>
                </div>
            </div>

            {/* Search Bar */}
            <div className="flex gap-3">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                    <input
                        type="text"
                        value={symbol}
                        onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                        onKeyDown={(e) => e.key === "Enter" && handleAnalyze(symbol)}
                        placeholder="Enter symbol (e.g. RELIANCE)"
                        className="w-full pl-10 pr-4 py-3 bg-white/5 border border-glass-border rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all text-sm font-mono"
                    />
                </div>
                <button
                    onClick={() => handleAnalyze(symbol)}
                    disabled={loading || !symbol.trim()}
                    className={cn(
                        "px-6 py-3 rounded-xl font-medium text-sm transition-all flex items-center gap-2",
                        loading
                            ? "bg-gray-700 text-gray-400 cursor-not-allowed"
                            : "bg-primary text-white hover:bg-primary/80 hover:shadow-[0_0_20px_rgba(6,182,212,0.3)]"
                    )}
                >
                    {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <BarChart3 className="h-4 w-4" />}
                    Analyze
                </button>
            </div>

            {/* Quick Symbols */}
            <div className="flex flex-wrap gap-2">
                {QUICK_SYMBOLS.map((s) => (
                    <button
                        key={s}
                        onClick={() => { setSymbol(s); handleAnalyze(s); }}
                        className={cn(
                            "px-3 py-1.5 rounded-lg text-xs font-medium border transition-all",
                            activeSymbol === s
                                ? "bg-primary/20 border-primary/40 text-primary"
                                : "bg-white/5 border-glass-border text-gray-400 hover:border-primary/30 hover:text-white"
                        )}
                    >
                        {s}
                    </button>
                ))}
            </div>

            {/* Error */}
            {error && (
                <div className="p-4 rounded-xl bg-accent/10 border border-accent/30 text-accent text-sm">
                    {error}
                </div>
            )}

            {/* Results */}
            {(signal || recommendation) && (
                <div className="grid gap-6 lg:grid-cols-5">
                    {/* Signal Panel — wider */}
                    <div className="lg:col-span-3">
                        {signal && activeSymbol && <SignalPanel signal={signal} symbol={activeSymbol} />}
                    </div>

                    {/* Side: Recommendation + Risk */}
                    <div className="lg:col-span-2 space-y-4">
                        {recommendation && <TradeRecommendation rec={recommendation} />}
                        <RiskDashboardPanel risk={risk} modules={modules} />
                    </div>
                </div>
            )}

            {/* Empty State */}
            {!signal && !recommendation && !loading && (
                <div className="flex flex-col items-center justify-center py-20 text-gray-500">
                    <BarChart3 className="h-12 w-12 mb-4 opacity-30" />
                    <p className="text-sm">Select a symbol above to run the signal engine</p>
                    <p className="text-xs text-gray-600 mt-1">Combines 7 institutional-grade indicators with multi-timeframe analysis</p>
                </div>
            )}
        </div>
    );
}
