"use client";

import { cn } from "@/lib/utils";
import { Target, TrendingUp, TrendingDown, Shield, Zap, BarChart3, Clock } from "lucide-react";
import type { TradeRecommendation as TradeRec } from "@/lib/api";

interface TradeRecommendationProps {
    rec: TradeRec;
}

export function TradeRecommendation({ rec }: TradeRecommendationProps) {
    const isLong = rec.signal?.direction === "LONG";
    const isApproved = rec.risk?.status?.includes("APPROVED");
    const modeColor =
        rec.mode?.mode === "FNO_NRML" ? "bg-secondary/20 text-secondary border-secondary/30" :
            rec.mode?.mode === "MIS" ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" :
                "bg-primary/20 text-primary border-primary/30";

    return (
        <div className={cn(
            "rounded-xl border bg-glass p-5 space-y-4 transition-all",
            isApproved ? "border-success/30" : "border-accent/30"
        )}>
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className={cn(
                        "flex h-12 w-12 items-center justify-center rounded-xl text-xl font-bold",
                        rec.score >= 85 ? "bg-success/20 text-success" :
                            rec.score >= 75 ? "bg-primary/20 text-primary" :
                                "bg-yellow-500/20 text-yellow-400"
                    )}>
                        {rec.score}
                    </div>
                    <div>
                        <h3 className="font-bold text-white text-xl">{rec.symbol}</h3>
                        <div className="flex items-center gap-2 mt-0.5">
                            <span className={cn(
                                "text-xs font-medium flex items-center gap-1",
                                isLong ? "text-success" : "text-accent"
                            )}>
                                {isLong ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                                {rec.setup_type}
                            </span>
                            <span className="text-gray-600">•</span>
                            <span className="text-xs text-gray-400 font-mono">
                                ₹{rec.price?.toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Risk Gate */}
                <div className={cn(
                    "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold border",
                    isApproved
                        ? "bg-success/10 text-success border-success/30"
                        : "bg-accent/10 text-accent border-accent/30"
                )}>
                    <Shield className="h-3.5 w-3.5" />
                    {isApproved ? "APPROVED" : "BLOCKED"}
                </div>
            </div>

            {/* Mode Badge */}
            <div className="flex items-center gap-3">
                <div className={cn("px-3 py-1.5 rounded-lg text-xs font-bold border", modeColor)}>
                    {rec.mode?.mode || "—"}
                </div>
                <span className="text-xs text-gray-400 flex-1">{rec.mode?.reason || ""}</span>
            </div>

            {/* Signal Confidence */}
            <div className="space-y-2">
                <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Signal Confidence</span>
                    <span className={cn("font-mono font-bold",
                        (rec.signal?.confidence ?? 0) >= 75 ? "text-success" :
                            (rec.signal?.confidence ?? 0) >= 50 ? "text-yellow-400" : "text-accent"
                    )}>
                        {rec.signal?.confidence || 0}%
                    </span>
                </div>
                <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div
                        className={cn(
                            "h-full rounded-full transition-all duration-500",
                            (rec.signal?.confidence ?? 0) >= 75 ? "bg-success" :
                                (rec.signal?.confidence ?? 0) >= 50 ? "bg-yellow-500" : "bg-accent"
                        )}
                        style={{ width: `${rec.signal?.confidence || 0}%` }}
                    />
                </div>
            </div>

            {/* Active Signals */}
            {rec.signal?.signals && rec.signal.signals.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                    {rec.signal.signals.slice(0, 5).map((s, i) => (
                        <span key={i} className="text-[10px] px-2 py-1 rounded-md bg-white/5 text-gray-400 border border-glass-border">
                            {s}
                        </span>
                    ))}
                </div>
            )}

            {/* Risk Reasons */}
            {rec.risk?.reasons && rec.risk.reasons.length > 0 && (
                <div className="space-y-1">
                    {rec.risk.reasons.map((r: string, i: number) => (
                        <div key={i} className="flex items-start gap-2 text-[11px] text-accent">
                            <span>⚠</span>
                            <span>{r}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
