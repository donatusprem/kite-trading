"use client";

import { useState, useEffect } from "react";
import {
    Search, RefreshCw, BarChart3, TrendingUp, TrendingDown, Zap, Shield,
    Activity, ArrowUpRight, Rocket, Filter, Clock, Wifi, WifiOff, ChevronRight
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useScannerData, ScanResult } from "@/hooks/useScannerData";
import CandlestickChart from "@/components/CandlestickChart";
import Link from "next/link";

// Map preset icon names to Lucide components
const ICON_MAP: Record<string, any> = {
    TrendingUp, TrendingDown, BarChart3, ArrowUpRight, Zap, Shield, Activity, Rocket,
};

// Fallback presets if API is offline
const FALLBACK_PRESETS: Record<string, { name: string; description: string; icon: string }> = {
    rsi_oversold: { name: "RSI Oversold Bounce", description: "RSI < 30 — reversal potential", icon: "TrendingUp" },
    rsi_overbought: { name: "RSI Overbought", description: "RSI > 70 — short or exit", icon: "TrendingDown" },
    volume_breakout: { name: "Volume Breakout", description: "Volume > 2x average", icon: "BarChart3" },
    ema_crossover: { name: "EMA Crossover (20/50)", description: "Bullish EMA cross", icon: "ArrowUpRight" },
    supertrend_buy: { name: "Supertrend Buy", description: "Supertrend flipped BUY", icon: "Zap" },
    near_support: { name: "Near Support Zone", description: "Price within 2% of support", icon: "Shield" },
    vwap_reclaim: { name: "VWAP Reclaim", description: "Price above VWAP", icon: "Activity" },
    strong_uptrend: { name: "Strong Uptrend", description: "HH + HL + EMA alignment", icon: "Rocket" },
};

const UNIVERSE_LABELS: Record<string, { label: string; desc: string }> = {
    quick: { label: "Quick 15", desc: "Top traded stocks" },
    nifty50: { label: "Nifty 50", desc: "Index constituents" },
    banknifty: { label: "Bank Nifty", desc: "Banking stocks" },
    fno: { label: "F&O Stocks", desc: "All F&O eligible" },
};

export default function ScannerPage() {
    const {
        results, presets, universes, loading, error, lastScanTime, scanMeta,
        runScan, startAutoRefresh, stopAutoRefresh
    } = useScannerData();

    const [selectedUniverse, setSelectedUniverse] = useState("quick");
    const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
    const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
    const [filterText, setFilterText] = useState("");
    const [autoRefresh, setAutoRefresh] = useState(false);
    const [sortBy, setSortBy] = useState<"score" | "rsi" | "volume">("score");

    // Merge API presets with fallback
    const displayPresets = Object.keys(FALLBACK_PRESETS).length > 0
        ? { ...FALLBACK_PRESETS, ...presets }
        : presets;

    // Auto-run scan on page load with quick preset
    useEffect(() => {
        // Don't auto-scan, just load presets
    }, []);

    const handleRunScan = (preset?: string) => {
        const p = preset ?? selectedPreset ?? undefined;
        setSelectedPreset(p ?? null);
        runScan(selectedUniverse, p);
    };

    const handleUniverseChange = (universe: string) => {
        setSelectedUniverse(universe);
        if (results.length > 0) {
            // Re-run with new universe
            runScan(universe, selectedPreset ?? undefined);
        }
    };

    const toggleAutoRefresh = () => {
        if (autoRefresh) {
            stopAutoRefresh();
            setAutoRefresh(false);
        } else {
            startAutoRefresh(selectedUniverse, selectedPreset ?? undefined, 60000);
            setAutoRefresh(true);
        }
    };

    // Filter & sort results
    const filteredResults = results
        .filter((r) => !filterText || r.symbol.toLowerCase().includes(filterText.toLowerCase()))
        .sort((a, b) => {
            if (sortBy === "rsi") return (a.indicators?.rsi ?? 50) - (b.indicators?.rsi ?? 50);
            if (sortBy === "volume") return (b.indicators?.volume_ratio ?? 0) - (a.indicators?.volume_ratio ?? 0);
            return b.score - a.score;
        });

    const timeSinceLastScan = lastScanTime
        ? `${Math.round((Date.now() - new Date(lastScanTime).getTime()) / 1000)}s ago`
        : null;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-white">Live Scanner</h1>
                    <p className="text-sm text-gray-400">
                        Streak-style screener • Select universe → pick preset → scan live
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    {timeSinceLastScan && (
                        <span className="flex items-center gap-1.5 text-xs text-gray-500">
                            <Clock className="h-3 w-3" /> Scanned {timeSinceLastScan}
                        </span>
                    )}
                    <button
                        onClick={toggleAutoRefresh}
                        className={cn(
                            "flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all",
                            autoRefresh
                                ? "bg-primary/20 border-primary/30 text-primary"
                                : "bg-white/5 border-glass-border text-gray-400 hover:text-white"
                        )}
                    >
                        {autoRefresh ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
                        {autoRefresh ? "Auto-refresh ON" : "Auto-refresh"}
                    </button>
                </div>
            </div>

            {/* Universe Tabs */}
            <div className="flex gap-2">
                {Object.entries(UNIVERSE_LABELS).map(([key, { label, desc }]) => (
                    <button
                        key={key}
                        onClick={() => handleUniverseChange(key)}
                        className={cn(
                            "px-4 py-2.5 rounded-xl text-sm font-medium border transition-all",
                            selectedUniverse === key
                                ? "bg-primary/20 border-primary/40 text-primary shadow-[0_0_15px_rgba(6,182,212,0.15)]"
                                : "bg-white/5 border-glass-border text-gray-400 hover:text-white hover:bg-white/10"
                        )}
                    >
                        <span className="block">{label}</span>
                        <span className="block text-[10px] opacity-60 mt-0.5">
                            {universes[key]?.count ?? desc}
                        </span>
                    </button>
                ))}
            </div>

            {/* Scanner Presets Gallery */}
            <div>
                <h2 className="text-sm font-medium text-gray-400 mb-3 uppercase tracking-wider">Scanner Presets</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {Object.entries(displayPresets).map(([key, preset]) => {
                        const IconComp = ICON_MAP[preset.icon] || Zap;
                        const isActive = selectedPreset === key;
                        return (
                            <button
                                key={key}
                                onClick={() => handleRunScan(key)}
                                disabled={loading}
                                className={cn(
                                    "relative group p-4 rounded-xl border text-left transition-all",
                                    isActive
                                        ? "bg-primary/15 border-primary/40 shadow-[0_0_20px_rgba(6,182,212,0.1)]"
                                        : "bg-white/[0.03] border-glass-border hover:bg-white/[0.06] hover:border-primary/20",
                                    loading && "opacity-50 cursor-wait"
                                )}
                            >
                                <div className={cn(
                                    "h-8 w-8 rounded-lg flex items-center justify-center mb-2",
                                    isActive ? "bg-primary/20 text-primary" : "bg-white/5 text-gray-400 group-hover:text-primary"
                                )}>
                                    <IconComp className="h-4 w-4" />
                                </div>
                                <h3 className={cn(
                                    "text-sm font-semibold",
                                    isActive ? "text-primary" : "text-white"
                                )}>
                                    {preset.name}
                                </h3>
                                <p className="text-[11px] text-gray-500 mt-0.5 line-clamp-1">
                                    {preset.description}
                                </p>
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* Run All Scan Button */}
            <div className="flex items-center gap-4">
                <button
                    onClick={() => handleRunScan()}
                    disabled={loading}
                    className={cn(
                        "flex items-center gap-2 px-6 py-2.5 rounded-xl font-bold text-sm transition-all",
                        loading
                            ? "bg-primary/30 text-primary/50 cursor-wait"
                            : "bg-primary text-black hover:bg-primary/90 shadow-[0_0_20px_rgba(6,182,212,0.3)] hover:shadow-[0_0_30px_rgba(6,182,212,0.5)]"
                    )}
                >
                    <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
                    {loading ? "Scanning..." : selectedPreset ? "Re-scan" : "Scan All"}
                </button>

                {scanMeta && (
                    <span className="text-xs text-gray-500">
                        {scanMeta.count} results from {UNIVERSE_LABELS[scanMeta.universe]?.label ?? scanMeta.universe}
                        {scanMeta.preset && ` • ${displayPresets[scanMeta.preset]?.name ?? scanMeta.preset}`}
                    </span>
                )}

                {results.length > 0 && (
                    <div className="ml-auto flex items-center gap-2">
                        <Filter className="h-3.5 w-3.5 text-gray-500" />
                        <div className="relative">
                            <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-gray-500" />
                            <input
                                type="text"
                                placeholder="Filter..."
                                value={filterText}
                                onChange={(e) => setFilterText(e.target.value)}
                                className="bg-black/20 border border-glass-border rounded-lg pl-7 pr-3 py-1.5 text-xs text-gray-300 w-40 focus:outline-none focus:border-primary/50"
                            />
                        </div>
                        <select
                            value={sortBy}
                            onChange={(e) => setSortBy(e.target.value as any)}
                            className="bg-black/20 border border-glass-border rounded-lg px-2 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-primary/50"
                        >
                            <option value="score">Sort: Score</option>
                            <option value="rsi">Sort: RSI</option>
                            <option value="volume">Sort: Volume</option>
                        </select>
                    </div>
                )}
            </div>

            {/* Chart Panel */}
            {selectedSymbol && (
                <CandlestickChart symbol={selectedSymbol} onClose={() => setSelectedSymbol(null)} />
            )}

            {/* Error */}
            {error && (
                <div className="p-4 rounded-xl border border-red-500/30 bg-red-500/10 text-red-400 text-sm">
                    <strong>Scan failed:</strong> {error}
                    <span className="block text-xs mt-1 opacity-70">Make sure the backend is running: python3 dashboard_api.py</span>
                </div>
            )}

            {/* Empty State */}
            {!loading && results.length === 0 && !error && (
                <div className="flex flex-col items-center justify-center h-64 border border-dashed border-glass-border rounded-xl">
                    <BarChart3 className="h-12 w-12 text-gray-600 mb-4" />
                    <h3 className="text-lg font-medium text-white">Select a preset to start scanning</h3>
                    <p className="text-gray-500 text-sm mt-1">
                        Pick a scanner preset above, choose your universe, and hit scan
                    </p>
                </div>
            )}

            {/* Loading State */}
            {loading && (
                <div className="flex flex-col items-center justify-center h-48 border border-dashed border-primary/20 rounded-xl bg-primary/[0.02]">
                    <RefreshCw className="h-8 w-8 text-primary animate-spin mb-3" />
                    <p className="text-primary text-sm font-medium">
                        Scanning {UNIVERSE_LABELS[selectedUniverse]?.label}...
                    </p>
                    <p className="text-gray-500 text-xs mt-1">Fetching live data from yfinance + Kite</p>
                </div>
            )}

            {/* Results Grid */}
            {!loading && filteredResults.length > 0 && (
                <div className="grid gap-3">
                    {/* Table Header */}
                    <div className="grid grid-cols-12 gap-4 px-5 py-2 text-[11px] text-gray-500 uppercase tracking-wider font-medium">
                        <div className="col-span-1">Score</div>
                        <div className="col-span-2">Symbol</div>
                        <div className="col-span-2">Indicators</div>
                        <div className="col-span-2">Signals</div>
                        <div className="col-span-2">Levels</div>
                        <div className="col-span-3 text-right">Actions</div>
                    </div>

                    {filteredResults.map((scan) => (
                        <div
                            key={scan.symbol}
                            className="group relative overflow-hidden rounded-xl border border-glass-border bg-glass transition-all hover:border-primary/30"
                        >
                            <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

                            <div className="relative grid grid-cols-12 gap-4 items-center p-4">
                                {/* Score */}
                                <div className="col-span-1">
                                    <div className={cn(
                                        "flex h-12 w-12 items-center justify-center rounded-full border-2 text-lg font-bold",
                                        scan.score >= 80 ? "border-success/40 text-success bg-success/10" :
                                            scan.score >= 60 ? "border-yellow-500/40 text-yellow-500 bg-yellow-500/10" :
                                                "border-gray-500/40 text-gray-400 bg-gray-500/10"
                                    )}>
                                        {scan.score}
                                    </div>
                                </div>

                                {/* Symbol + Price */}
                                <div className="col-span-2">
                                    <h3 className="text-lg font-bold text-white">{scan.symbol}</h3>
                                    <div className="text-xl font-mono text-gray-200">
                                        ₹{(scan.ltp ?? 0).toLocaleString()}
                                    </div>
                                    <span className={cn(
                                        "text-[10px] font-medium px-1.5 py-0.5 rounded mt-1 inline-block",
                                        scan.trend === "Uptrend" ? "bg-success/10 text-success" :
                                            scan.trend === "Downtrend" ? "bg-red-500/10 text-red-400" :
                                                "bg-gray-500/10 text-gray-400"
                                    )}>
                                        {scan.trend}
                                    </span>
                                </div>

                                {/* Key Indicators */}
                                <div className="col-span-2 space-y-1">
                                    {scan.indicators && (
                                        <>
                                            <div className="flex justify-between text-xs">
                                                <span className="text-gray-500">RSI</span>
                                                <span className={cn(
                                                    "font-mono",
                                                    scan.indicators.rsi > 70 ? "text-red-400" :
                                                        scan.indicators.rsi < 30 ? "text-success" : "text-gray-300"
                                                )}>
                                                    {scan.indicators.rsi}
                                                </span>
                                            </div>
                                            <div className="flex justify-between text-xs">
                                                <span className="text-gray-500">Vol Ratio</span>
                                                <span className={cn(
                                                    "font-mono",
                                                    scan.indicators.volume_ratio > 2 ? "text-primary" : "text-gray-300"
                                                )}>
                                                    {scan.indicators.volume_ratio}x
                                                </span>
                                            </div>
                                            <div className="flex justify-between text-xs">
                                                <span className="text-gray-500">Supertrend</span>
                                                <span className={cn(
                                                    "font-mono text-[11px]",
                                                    scan.indicators.supertrend === "buy" ? "text-success" : "text-red-400"
                                                )}>
                                                    {scan.indicators.supertrend.toUpperCase()}
                                                </span>
                                            </div>
                                        </>
                                    )}
                                </div>

                                {/* Signals */}
                                <div className="col-span-2 space-y-1">
                                    {(scan.signals || []).slice(0, 3).map((sig, i) => (
                                        <div key={i} className="flex items-center gap-1.5 text-xs text-gray-300">
                                            <div className="h-1 w-1 rounded-full bg-primary flex-shrink-0" />
                                            <span className="truncate">{sig}</span>
                                        </div>
                                    ))}
                                </div>

                                {/* Levels */}
                                <div className="col-span-2 space-y-1 text-xs">
                                    <div className="flex justify-between">
                                        <span className="text-gray-500">Stop</span>
                                        <span className="text-accent font-mono">₹{scan.stopLoss}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-500">Target</span>
                                        <span className="text-primary font-mono">₹{scan.target1}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-500">R:R</span>
                                        <span className="text-gray-300 font-mono">
                                            {scan.ltp && scan.stopLoss && scan.target1
                                                ? `1:${((scan.target1 - scan.ltp) / ((scan.ltp - scan.stopLoss) || 1)).toFixed(1)}`
                                                : "--"
                                            }
                                        </span>
                                    </div>
                                </div>

                                {/* Actions */}
                                <div className="col-span-3 flex items-center justify-end gap-2">
                                    <button
                                        onClick={() => setSelectedSymbol(selectedSymbol === scan.symbol ? null : scan.symbol)}
                                        className={cn(
                                            "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium border transition-all",
                                            selectedSymbol === scan.symbol
                                                ? "bg-primary/20 text-primary border-primary/30"
                                                : "bg-white/5 text-gray-400 hover:text-white border-glass-border"
                                        )}
                                    >
                                        <BarChart3 className="h-3 w-3" />
                                        Chart
                                    </button>
                                    <Link
                                        href={`/signals?symbol=${scan.symbol}`}
                                        className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 transition-all"
                                    >
                                        Deep Analyze <ChevronRight className="h-3 w-3" />
                                    </Link>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
