"use client";

import { useState, useCallback, useEffect } from "react";
import {
    TrendingUp, TrendingDown, BarChart3, Activity, Target, Shield, RefreshCw,
    Loader2, ArrowUpDown, Zap
} from "lucide-react";
import { cn } from "@/lib/utils";

const API_BASE = "http://localhost:8000";

const UNDERLYINGS = ["NIFTY", "BANKNIFTY", "FINNIFTY"];
const EXPIRY_OPTIONS = [
    { value: "weekly", label: "Weekly" },
    { value: "next_week", label: "Next Week" },
    { value: "monthly", label: "Monthly" },
];

interface ChainData {
    underlying: string;
    spot_price: number;
    expiry: string;
    strikes: number[];
    calls: Record<string, any>;
    puts: Record<string, any>;
    atm_strike: number;
}

interface OIData {
    pcr: number;
    sentiment: string;
    sentiment_note: string;
    total_call_oi: number;
    total_put_oi: number;
    max_call_oi_strike: number;
    max_put_oi_strike: number;
    resistance_zone: number;
    support_zone: number;
    range: string;
    spot_price: number;
}

export default function OptionsPage() {
    const [underlying, setUnderlying] = useState("NIFTY");
    const [expiry, setExpiry] = useState("weekly");
    const [chain, setChain] = useState<ChainData | null>(null);
    const [oi, setOI] = useState<OIData | null>(null);
    const [recommendation, setRecommendation] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [oiLoading, setOILoading] = useState(false);
    const [recLoading, setRecLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [direction, setDirection] = useState<"LONG" | "SHORT">("LONG");
    const [score, setScore] = useState(85);

    const fetchChain = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_BASE}/options/chain?underlying=${underlying}&expiry=${expiry}`);
            const data = await res.json();
            if (data.error) { setError(data.error); setChain(null); }
            else setChain(data);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, [underlying, expiry]);

    const fetchOI = async () => {
        setOILoading(true);
        try {
            const res = await fetch(`${API_BASE}/options/oi?underlying=${underlying}&expiry=${expiry}`);
            const data = await res.json();
            if (data.oi_analysis) setOI(data.oi_analysis);
        } catch (e: any) {
            console.error(e);
        } finally {
            setOILoading(false);
        }
    };

    const fetchRecommendation = async () => {
        setRecLoading(true);
        try {
            const res = await fetch(`${API_BASE}/options/recommend`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ underlying, direction, score }),
            });
            const data = await res.json();
            setRecommendation(data.recommendation);
        } catch (e: any) {
            console.error(e);
        } finally {
            setRecLoading(false);
        }
    };

    useEffect(() => { fetchChain(); }, [fetchChain]);

    const spotPrice = chain?.spot_price || 0;
    const atmStrike = chain?.atm_strike || 0;

    // Get visible strikes around ATM (±8)
    const visibleStrikes = (chain?.strikes || []).filter((s) => {
        if (!atmStrike) return true;
        return Math.abs(s - atmStrike) <= 800;
    }).slice(0, 16);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                        <TrendingUp className="h-6 w-6 text-primary" />
                        Options Analyzer
                    </h1>
                    <p className="text-sm text-gray-400 mt-1">
                        Chain view, OI analysis, and AI-powered strike selection
                    </p>
                </div>
                <button
                    onClick={fetchChain}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-primary/10 border border-primary/30 text-primary text-sm font-medium hover:bg-primary/20 transition-all"
                >
                    {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                    Refresh
                </button>
            </div>

            {/* Controls */}
            <div className="flex flex-wrap gap-3">
                {/* Underlying Tabs */}
                <div className="flex bg-black/30 rounded-xl border border-glass-border p-1">
                    {UNDERLYINGS.map((u) => (
                        <button
                            key={u}
                            onClick={() => setUnderlying(u)}
                            className={cn(
                                "px-4 py-2 rounded-lg text-xs font-bold transition-all",
                                underlying === u
                                    ? "bg-primary/20 text-primary shadow-[0_0_10px_rgba(6,182,212,0.2)]"
                                    : "text-gray-500 hover:text-white"
                            )}
                        >
                            {u}
                        </button>
                    ))}
                </div>

                {/* Expiry Selector */}
                <div className="flex bg-black/30 rounded-xl border border-glass-border p-1">
                    {EXPIRY_OPTIONS.map((e) => (
                        <button
                            key={e.value}
                            onClick={() => setExpiry(e.value)}
                            className={cn(
                                "px-3 py-2 rounded-lg text-xs font-medium transition-all",
                                expiry === e.value
                                    ? "bg-secondary/20 text-secondary"
                                    : "text-gray-500 hover:text-white"
                            )}
                        >
                            {e.label}
                        </button>
                    ))}
                </div>

                {/* Spot Price */}
                {spotPrice > 0 && (
                    <div className="flex items-center gap-2 px-4 py-2 rounded-xl border border-glass-border bg-glass">
                        <span className="text-xs text-gray-500">Spot</span>
                        <span className="text-sm font-mono font-bold text-white">
                            ₹{spotPrice.toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                        </span>
                    </div>
                )}

                {chain?.expiry && (
                    <div className="flex items-center gap-2 px-4 py-2 rounded-xl border border-glass-border bg-glass">
                        <span className="text-xs text-gray-500">Expiry</span>
                        <span className="text-sm font-mono text-yellow-400">{chain.expiry}</span>
                    </div>
                )}
            </div>

            {error && (
                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                    ⚠️ {error}
                </div>
            )}

            {/* Main Grid */}
            <div className="grid gap-6 lg:grid-cols-3">
                {/* Option Chain Table — 2 cols */}
                <div className="lg:col-span-2 rounded-xl border border-glass-border bg-glass overflow-hidden">
                    <div className="flex items-center justify-between p-4 border-b border-glass-border/50">
                        <h3 className="text-sm font-bold text-white flex items-center gap-2">
                            <ArrowUpDown className="h-4 w-4 text-primary" />
                            Option Chain
                        </h3>
                        <span className="text-[10px] text-gray-500">{visibleStrikes.length} strikes shown</span>
                    </div>

                    {loading ? (
                        <div className="flex items-center justify-center py-16">
                            <Loader2 className="h-6 w-6 text-primary animate-spin" />
                        </div>
                    ) : visibleStrikes.length > 0 ? (
                        <div className="overflow-x-auto">
                            <table className="w-full text-xs">
                                <thead>
                                    <tr className="border-b border-glass-border/50">
                                        <th className="text-right p-2 text-success font-medium">CE OI</th>
                                        <th className="text-right p-2 text-success font-medium">CE LTP</th>
                                        <th className="text-center p-2 text-white font-bold bg-white/5">Strike</th>
                                        <th className="text-left p-2 text-accent font-medium">PE LTP</th>
                                        <th className="text-left p-2 text-accent font-medium">PE OI</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {visibleStrikes.map((strike) => {
                                        const call = chain?.calls?.[String(strike)];
                                        const put = chain?.puts?.[String(strike)];
                                        const isATM = strike === atmStrike;
                                        const isITM_CE = strike < spotPrice;
                                        const isITM_PE = strike > spotPrice;

                                        return (
                                            <tr
                                                key={strike}
                                                className={cn(
                                                    "border-b border-glass-border/20 hover:bg-white/5 transition-colors",
                                                    isATM && "bg-primary/5 border-primary/20"
                                                )}
                                            >
                                                <td className={cn("text-right p-2 font-mono", isITM_CE ? "text-success/40" : "text-success")}>
                                                    {call?.oi ? (call.oi / 1000).toFixed(0) + "K" : "—"}
                                                </td>
                                                <td className={cn("text-right p-2 font-mono font-medium", isITM_CE ? "text-gray-600" : "text-white")}>
                                                    {call?.last_price?.toFixed(2) || call?.premium?.toFixed(2) || "—"}
                                                </td>
                                                <td className={cn(
                                                    "text-center p-2 font-mono font-bold bg-white/5",
                                                    isATM ? "text-primary" : "text-gray-300"
                                                )}>
                                                    {strike}
                                                    {isATM && <span className="text-[8px] text-primary ml-1">ATM</span>}
                                                </td>
                                                <td className={cn("text-left p-2 font-mono font-medium", isITM_PE ? "text-gray-600" : "text-white")}>
                                                    {put?.last_price?.toFixed(2) || put?.premium?.toFixed(2) || "—"}
                                                </td>
                                                <td className={cn("text-left p-2 font-mono", isITM_PE ? "text-accent/40" : "text-accent")}>
                                                    {put?.oi ? (put.oi / 1000).toFixed(0) + "K" : "—"}
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center py-16 text-gray-500">
                            <BarChart3 className="h-8 w-8 mb-3 opacity-30" />
                            <p className="text-xs">No chain data available</p>
                            <p className="text-[10px] text-gray-600 mt-1">Click Refresh or check Kite connection</p>
                        </div>
                    )}
                </div>

                {/* Right Panel: OI + Recommendation */}
                <div className="space-y-4">
                    {/* OI Analysis Card */}
                    <div className="rounded-xl border border-glass-border bg-glass p-4 space-y-3">
                        <div className="flex items-center justify-between">
                            <h3 className="text-sm font-bold text-white flex items-center gap-2">
                                <Activity className="h-4 w-4 text-primary" />
                                OI Analysis
                            </h3>
                            <button
                                onClick={fetchOI}
                                disabled={oiLoading}
                                className="text-[10px] text-primary hover:text-primary/80"
                            >
                                {oiLoading ? "Loading..." : "Fetch OI"}
                            </button>
                        </div>

                        {oi ? (
                            <div className="space-y-2">
                                <div className="flex justify-between text-xs">
                                    <span className="text-gray-500">PCR</span>
                                    <span className={cn("font-mono font-bold",
                                        oi.pcr > 1.2 ? "text-success" : oi.pcr < 0.7 ? "text-accent" : "text-yellow-400"
                                    )}>
                                        {oi.pcr}
                                    </span>
                                </div>
                                <div className="flex justify-between text-xs">
                                    <span className="text-gray-500">Sentiment</span>
                                    <span className={cn("font-bold text-[10px] px-2 py-0.5 rounded",
                                        oi.sentiment === "BULLISH" ? "bg-success/20 text-success" :
                                            oi.sentiment === "BEARISH" ? "bg-accent/20 text-accent" :
                                                "bg-yellow-500/20 text-yellow-400"
                                    )}>
                                        {oi.sentiment}
                                    </span>
                                </div>
                                <div className="text-[10px] text-gray-500 italic">{oi.sentiment_note}</div>
                                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-glass-border/50">
                                    <div className="text-center p-2 rounded-lg bg-success/5 border border-success/10">
                                        <div className="text-[10px] text-gray-500">Support</div>
                                        <div className="text-sm font-mono font-bold text-success">{oi.support_zone}</div>
                                    </div>
                                    <div className="text-center p-2 rounded-lg bg-accent/5 border border-accent/10">
                                        <div className="text-[10px] text-gray-500">Resistance</div>
                                        <div className="text-sm font-mono font-bold text-accent">{oi.resistance_zone}</div>
                                    </div>
                                </div>
                                <div className="flex justify-between text-[10px] text-gray-500">
                                    <span>CE OI: {(oi.total_call_oi / 1000).toFixed(0)}K</span>
                                    <span>PE OI: {(oi.total_put_oi / 1000).toFixed(0)}K</span>
                                </div>
                            </div>
                        ) : (
                            <div className="text-center py-4 text-[10px] text-gray-600">
                                Click &quot;Fetch OI&quot; to analyze open interest
                            </div>
                        )}
                    </div>

                    {/* Trade Recommendation */}
                    <div className="rounded-xl border border-glass-border bg-glass p-4 space-y-3">
                        <h3 className="text-sm font-bold text-white flex items-center gap-2">
                            <Target className="h-4 w-4 text-secondary" />
                            AI Strike Selector
                        </h3>

                        <div className="flex gap-2">
                            <button
                                onClick={() => setDirection("LONG")}
                                className={cn(
                                    "flex-1 py-2 rounded-lg text-xs font-bold border transition-all",
                                    direction === "LONG"
                                        ? "bg-success/20 text-success border-success/30"
                                        : "bg-white/5 text-gray-500 border-glass-border"
                                )}
                            >
                                <TrendingUp className="h-3 w-3 inline mr-1" />
                                LONG
                            </button>
                            <button
                                onClick={() => setDirection("SHORT")}
                                className={cn(
                                    "flex-1 py-2 rounded-lg text-xs font-bold border transition-all",
                                    direction === "SHORT"
                                        ? "bg-accent/20 text-accent border-accent/30"
                                        : "bg-white/5 text-gray-500 border-glass-border"
                                )}
                            >
                                <TrendingDown className="h-3 w-3 inline mr-1" />
                                SHORT
                            </button>
                        </div>

                        <div className="flex items-center justify-between text-xs">
                            <span className="text-gray-500">Score</span>
                            <input
                                type="number"
                                value={score}
                                onChange={(e) => setScore(Number(e.target.value))}
                                className="w-16 bg-black/30 border border-glass-border rounded px-2 py-1 text-white text-right font-mono text-xs focus:outline-none"
                            />
                        </div>

                        <button
                            onClick={fetchRecommendation}
                            disabled={recLoading}
                            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-secondary/10 border border-secondary/30 text-secondary hover:bg-secondary/20 transition-all text-xs font-bold"
                        >
                            {recLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Zap className="h-3 w-3" />}
                            {recLoading ? "Analyzing..." : "Get Recommendation"}
                        </button>

                        {recommendation && (
                            <div className="space-y-2 pt-2 border-t border-glass-border/50">
                                {recommendation.action === "TRADE" ? (
                                    <>
                                        <div className="flex items-center gap-2">
                                            <Shield className="h-3 w-3 text-success" />
                                            <span className="text-xs font-bold text-success">TRADE SIGNAL</span>
                                        </div>
                                        <div className="text-[10px] text-gray-300 font-mono leading-relaxed">
                                            {recommendation.summary}
                                        </div>
                                        {recommendation.option && (
                                            <div className="grid grid-cols-2 gap-1.5 text-[10px]">
                                                <div className="p-1.5 rounded bg-white/5">
                                                    <span className="text-gray-500">Symbol</span>
                                                    <div className="text-white font-mono">{recommendation.option.tradingsymbol}</div>
                                                </div>
                                                <div className="p-1.5 rounded bg-white/5">
                                                    <span className="text-gray-500">Premium</span>
                                                    <div className="text-white font-mono">₹{recommendation.position?.premium}</div>
                                                </div>
                                                <div className="p-1.5 rounded bg-white/5">
                                                    <span className="text-gray-500">Stop Loss</span>
                                                    <div className="text-accent font-mono">₹{recommendation.exit_levels?.stop_loss}</div>
                                                </div>
                                                <div className="p-1.5 rounded bg-white/5">
                                                    <span className="text-gray-500">Target 1</span>
                                                    <div className="text-success font-mono">₹{recommendation.exit_levels?.target_1}</div>
                                                </div>
                                            </div>
                                        )}
                                    </>
                                ) : (
                                    <div className="text-xs text-gray-400">
                                        <span className="font-bold text-yellow-400">{recommendation.action}</span>
                                        {" — "}{recommendation.reason}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
