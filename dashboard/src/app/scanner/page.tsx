"use client";

import { useState } from "react";
import { Search, Filter, RefreshCw, ArrowRight, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import { useSystemData } from "@/hooks/useSystemData";

export default function ScannerPage() {
    const [isRefreshing, setIsRefreshing] = useState(false);
    const { latestScan, isConnected } = useSystemData();

    const handleRefresh = async () => {
        setIsRefreshing(true);
        try {
            await fetch("http://localhost:8000/scan/trigger", { method: "POST" });
        } catch (e) {
            console.error("Scan trigger failed:", e);
        }
        // Give the backend a moment to save results, then the useSystemData hook will pick it up
        setTimeout(() => setIsRefreshing(false), 2000);
    };

    const scanData = Array.isArray(latestScan?.data) ? latestScan.data : [];

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-white">Live Market Scanner</h1>
                    <p className="text-sm text-gray-400">Real-time opportunities detected by AI</p>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={handleRefresh}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border border-glass-border text-gray-300 hover:bg-white/10 hover:text-white transition-all"
                    >
                        <RefreshCw className={cn("h-4 w-4", isRefreshing && "animate-spin")} />
                        Refresh
                    </button>
                    <div className={cn("flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium", isConnected ? "bg-primary/20 border-primary/30 text-primary" : "bg-red-500/20 border-red-500/30 text-red-400")}>
                        <span className="relative flex h-2 w-2">
                            <span className={cn("animate-ping absolute inline-flex h-full w-full rounded-full opacity-75", isConnected ? "bg-primary" : "bg-red-500")}></span>
                            <span className={cn("relative inline-flex rounded-full h-2 w-2", isConnected ? "bg-primary" : "bg-red-500")}></span>
                        </span>
                        {isConnected ? "Live Scanning" : "Offline"}
                    </div>
                </div>
            </div>

            {/* Filters */}
            <div className="flex items-center gap-4 py-4 border-y border-glass-border">
                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-500" />
                    <input
                        type="text"
                        placeholder="Filter by symbol..."
                        className="w-full bg-black/20 border border-glass-border rounded-lg pl-9 pr-4 py-2 text-sm text-gray-300 focus:outline-none focus:border-primary/50"
                    />
                </div>
                <button className="flex items-center gap-2 px-3 py-2 text-sm text-gray-400 hover:text-white">
                    <Filter className="h-4 w-4" />
                    Score &gt; 80
                </button>
            </div>

            {/* Results Grid */}
            <div className="grid gap-4">
                {!isConnected && (
                    <div className="flex flex-col items-center justify-center h-64 border border-dashed border-glass-border rounded-xl">
                        <AlertTriangle className="h-10 w-10 text-yellow-500 mb-4" />
                        <h3 className="text-lg font-medium text-white">System Offline</h3>
                        <p className="text-gray-400 text-sm">Start the backend to receive live scans.</p>
                    </div>
                )}

                {isConnected && scanData.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-64 border border-dashed border-glass-border rounded-xl">
                        <h3 className="text-lg font-medium text-white">No active setups</h3>
                        <p className="text-gray-400 text-sm">AI is scanning... wait for alerts.</p>
                    </div>
                )}

                {scanData.map((scan: any) => (
                    <div key={scan.symbol} className="group relative overflow-hidden rounded-xl border border-glass-border bg-glass p-1 transition-all hover:border-primary/50">
                        <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>

                        <div className="relative flex flex-col md:flex-row items-center gap-6 p-5">
                            {/* Score Circle */}
                            <div className="flex-shrink-0">
                                <div className={cn(
                                    "relative flex h-16 w-16 items-center justify-center rounded-full border-4 text-xl font-bold backdrop-blur-sm",
                                    (scan.score || 0) >= 80 ? "border-success/30 text-success bg-success/10" :
                                        (scan.score || 0) >= 50 ? "border-yellow-500/30 text-yellow-500 bg-yellow-500/10" :
                                            "border-gray-500/30 text-gray-500 bg-gray-500/10"
                                )}>
                                    {scan.score || 0}
                                    <div className="absolute -bottom-2 text-[10px] uppercase font-medium tracking-wide">Score</div>
                                </div>
                            </div>

                            {/* Main Info */}
                            <div className="flex-1 min-w-0 grid md:grid-cols-3 gap-6 items-center">
                                <div>
                                    <div className="flex items-baseline gap-2">
                                        <h3 className="text-xl font-bold text-white">{scan.symbol}</h3>
                                        <span className="text-xs text-gray-400">{scan.timestamp}</span>
                                    </div>
                                    <div className="text-2xl font-mono text-gray-200">₹{scan.ltp?.toLocaleString() ?? "--"}</div>
                                </div>

                                <div className="space-y-1">
                                    {/* Assuming signals is an array in real data, or fallback */}
                                    {(scan.signals || [scan.pattern]).map((sig: string, i: number) => (
                                        <div key={i} className="flex items-center gap-2 text-sm text-gray-300">
                                            <div className="h-1.5 w-1.5 rounded-full bg-primary"></div>
                                            {sig}
                                        </div>
                                    ))}
                                </div>

                                <div className="space-y-2 text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-gray-500">Trend</span>
                                        <span className="text-success font-medium">{scan.trend || "Neutral"}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-500">Stop Loss</span>
                                        <span className="text-accent font-mono">₹{scan.stopLoss || "--"}</span>
                                    </div>
                                </div>
                            </div>

                            {/* Action */}
                            <div className="flex-shrink-0 pl-6 border-l border-glass-border">
                                <button className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 font-bold text-black hover:bg-primary/90 transition-colors shadow-[0_0_15px_rgba(6,182,212,0.3)] hover:shadow-[0_0_25px_rgba(6,182,212,0.5)]">
                                    Execute <ArrowRight className="h-4 w-4" />
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
