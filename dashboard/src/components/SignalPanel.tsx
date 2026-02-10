"use client";

import { cn } from "@/lib/utils";
import {
    TrendingUp, TrendingDown, Minus, Activity, BarChart3,
    ArrowUpRight, ArrowDownRight, Gauge, Waves, Zap
} from "lucide-react";
import type { SignalAnalysis } from "@/lib/api";

interface SignalPanelProps {
    signal: SignalAnalysis;
    symbol: string;
}

function IndicatorBadge({ label, value, color }: { label: string; value: string; color: string }) {
    return (
        <div className={cn(
            "flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium",
            color === "green" && "bg-success/10 border-success/20 text-success",
            color === "red" && "bg-accent/10 border-accent/20 text-accent",
            color === "yellow" && "bg-yellow-500/10 border-yellow-500/20 text-yellow-400",
            color === "blue" && "bg-primary/10 border-primary/20 text-primary",
            color === "gray" && "bg-white/5 border-glass-border text-gray-400",
        )}>
            <span className="text-gray-500">{label}</span>
            <span className="font-mono">{value}</span>
        </div>
    );
}

export function SignalPanel({ signal, symbol }: SignalPanelProps) {
    const dirIcon = signal.direction === "LONG"
        ? <TrendingUp className="h-5 w-5" />
        : signal.direction === "SHORT"
            ? <TrendingDown className="h-5 w-5" />
            : <Minus className="h-5 w-5" />;

    const dirColor = signal.direction === "LONG" ? "text-success" : signal.direction === "SHORT" ? "text-accent" : "text-yellow-400";
    const confColor = signal.confidence >= 75 ? "text-success" : signal.confidence >= 50 ? "text-yellow-400" : "text-accent";

    return (
        <div className="rounded-xl border border-glass-border bg-glass p-5 space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className={cn("p-2 rounded-lg bg-white/5", dirColor)}>
                        {dirIcon}
                    </div>
                    <div>
                        <h3 className="font-bold text-white text-lg">{symbol}</h3>
                        <span className={cn("text-xs font-medium", dirColor)}>
                            {signal.direction} • {signal.trend_strength}
                        </span>
                    </div>
                </div>
                <div className="text-right">
                    <div className={cn("text-3xl font-bold font-mono", confColor)}>
                        {signal.confidence}%
                    </div>
                    <div className="text-[10px] text-gray-500 uppercase tracking-wide">Confidence</div>
                </div>
            </div>

            {/* Confidence Bar */}
            <div className="relative h-2 bg-gray-800 rounded-full overflow-hidden">
                <div
                    className={cn(
                        "h-full rounded-full transition-all duration-700",
                        signal.confidence >= 75 ? "bg-gradient-to-r from-success to-emerald-300" :
                            signal.confidence >= 50 ? "bg-gradient-to-r from-yellow-500 to-amber-300" :
                                "bg-gradient-to-r from-accent to-red-300"
                    )}
                    style={{ width: `${signal.confidence}%` }}
                />
                {/* Threshold markers */}
                <div className="absolute top-0 left-[50%] h-full w-px bg-gray-600" />
                <div className="absolute top-0 left-[75%] h-full w-px bg-gray-600" />
            </div>

            {/* Indicator Grid */}
            <div className="grid grid-cols-2 gap-2">
                <IndicatorBadge
                    label="VWAP"
                    value={signal.vwap?.position || "—"}
                    color={signal.vwap?.position === "above" ? "green" : signal.vwap?.position === "below" ? "red" : "gray"}
                />
                <IndicatorBadge
                    label="RSI"
                    value={`${signal.rsi?.value?.toFixed(1) || "—"} ${signal.rsi?.zone || ""}`}
                    color={signal.rsi?.zone === "oversold" ? "green" : signal.rsi?.zone === "overbought" ? "red" : "blue"}
                />
                <IndicatorBadge
                    label="Supertrend"
                    value={signal.supertrend?.signal || "—"}
                    color={signal.supertrend?.signal === "BULLISH" ? "green" : signal.supertrend?.signal === "BEARISH" ? "red" : "gray"}
                />
                <IndicatorBadge
                    label="EMA"
                    value={signal.ema?.trend || "—"}
                    color={signal.ema?.trend === "BULLISH" ? "green" : signal.ema?.trend === "BEARISH" ? "red" : "yellow"}
                />
                <IndicatorBadge
                    label="ATR"
                    value={`${signal.atr?.pct?.toFixed(2) || "—"}%`}
                    color="blue"
                />
                <IndicatorBadge
                    label="Volume"
                    value={`${signal.volume?.ratio?.toFixed(1) || "—"}x ${signal.volume?.surge ? "🔥" : ""}`}
                    color={signal.volume?.surge ? "green" : "gray"}
                />
            </div>

            {/* Bull/Bear Score Bar */}
            <div className="space-y-1">
                <div className="flex justify-between text-[10px] text-gray-500 uppercase tracking-wider">
                    <span>Bull {signal.scores?.bull || 0}</span>
                    <span>Bear {signal.scores?.bear || 0}</span>
                </div>
                <div className="flex h-3 rounded-full overflow-hidden bg-gray-800">
                    <div
                        className="bg-gradient-to-r from-success to-emerald-400 transition-all duration-500"
                        style={{ width: `${((signal.scores?.bull || 0) / Math.max((signal.scores?.bull || 0) + (signal.scores?.bear || 0), 1)) * 100}%` }}
                    />
                    <div
                        className="bg-gradient-to-r from-red-400 to-accent transition-all duration-500"
                        style={{ width: `${((signal.scores?.bear || 0) / Math.max((signal.scores?.bull || 0) + (signal.scores?.bear || 0), 1)) * 100}%` }}
                    />
                </div>
            </div>

            {/* Signals List */}
            {signal.signals && signal.signals.length > 0 && (
                <div className="space-y-1.5">
                    <div className="text-[10px] text-gray-500 uppercase tracking-wider">Active Signals</div>
                    {signal.signals.map((s, i) => (
                        <div key={i} className="flex items-start gap-2 text-xs text-gray-300">
                            <Zap className="h-3 w-3 text-primary mt-0.5 flex-shrink-0" />
                            <span>{s}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Divergence Alert */}
            {signal.rsi?.divergence?.type && signal.rsi.divergence.type !== "none" && (
                <div className={cn(
                    "flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium animate-pulse",
                    signal.rsi.divergence.type === "bullish" ? "bg-success/10 border border-success/30 text-success" : "bg-accent/10 border border-accent/30 text-accent"
                )}>
                    <Activity className="h-4 w-4" />
                    {signal.rsi.divergence.type.toUpperCase()} DIVERGENCE DETECTED
                </div>
            )}
        </div>
    );
}
