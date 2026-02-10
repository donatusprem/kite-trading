"use client";

import { cn } from "@/lib/utils";
import { Shield, Thermometer, AlertTriangle, TrendingDown, Calculator, Server } from "lucide-react";
import type { RiskDashboard as RiskData, ModuleStatus } from "@/lib/api";

interface RiskDashboardProps {
    risk: RiskData | null;
    modules: ModuleStatus | null;
}

function HeatGauge({ pct, status }: { pct: number; status: string }) {
    const clampedPct = Math.min(pct, 100);
    const color = status === "SAFE" ? "bg-success" :
        status === "ELEVATED" ? "bg-yellow-500" :
            status === "WARNING" ? "bg-orange-500" : "bg-accent";
    const textColor = status === "SAFE" ? "text-success" :
        status === "ELEVATED" ? "text-yellow-400" :
            status === "WARNING" ? "text-orange-400" : "text-accent";

    return (
        <div className="space-y-2">
            <div className="flex justify-between items-baseline">
                <div className="flex items-center gap-2">
                    <Thermometer className={cn("h-4 w-4", textColor)} />
                    <span className="text-sm font-medium text-white">Portfolio Heat</span>
                </div>
                <span className={cn("text-lg font-bold font-mono", textColor)}>
                    {pct.toFixed(1)}%
                </span>
            </div>
            <div className="relative h-3 bg-gray-800 rounded-full overflow-hidden">
                {/* Zone markers */}
                <div className="absolute inset-0 flex">
                    <div className="w-1/3 border-r border-gray-700" />
                    <div className="w-1/3 border-r border-gray-700" />
                    <div className="w-1/3" />
                </div>
                <div
                    className={cn("h-full rounded-full transition-all duration-700", color)}
                    style={{ width: `${clampedPct}%` }}
                />
            </div>
            <div className="flex justify-between text-[9px] text-gray-600 uppercase">
                <span>Safe</span>
                <span>Elevated</span>
                <span>Danger</span>
            </div>
        </div>
    );
}

export function RiskDashboardPanel({ risk, modules }: RiskDashboardProps) {
    if (!risk) {
        return (
            <div className="rounded-xl border border-glass-border bg-glass p-5">
                <div className="flex items-center gap-2 text-gray-500 text-sm">
                    <Shield className="h-4 w-4" />
                    Loading risk data...
                </div>
            </div>
        );
    }

    const rawHeat = risk.portfolio_heat || {};
    const heat = {
        current_pct: rawHeat.current_pct ?? 0,
        status: rawHeat.status ?? "SAFE",
        remaining_budget: rawHeat.remaining_budget ?? 0,
    };
    const rawDrawdown = risk.drawdown || {};
    const drawdown = {
        status: rawDrawdown.status ?? "TRADING_ALLOWED",
        daily_pct: rawDrawdown.daily_pct ?? 0,
        weekly_pct: rawDrawdown.weekly_pct ?? 0,
    };

    return (
        <div className="rounded-xl border border-glass-border bg-glass p-5 space-y-5">
            {/* Title */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Shield className="h-5 w-5 text-primary" />
                    <h3 className="font-semibold text-white">Risk Dashboard</h3>
                </div>
                <span className={cn(
                    "text-xs px-2 py-1 rounded-full font-medium",
                    drawdown.status === "TRADING_ALLOWED"
                        ? "bg-success/10 text-success"
                        : "bg-accent/10 text-accent"
                )}>
                    {drawdown.status === "TRADING_ALLOWED" ? "Trading Active" : "⚠️ Breaker Tripped"}
                </span>
            </div>

            {/* Heat Gauge */}
            <HeatGauge pct={heat.current_pct} status={heat.status} />

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-lg bg-white/5 border border-glass-border">
                    <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Daily Drawdown</div>
                    <div className={cn(
                        "text-lg font-bold font-mono",
                        Math.abs(drawdown.daily_pct) > 2 ? "text-accent" : "text-white"
                    )}>
                        {(drawdown.daily_pct ?? 0).toFixed(1)}%
                    </div>
                </div>
                <div className="p-3 rounded-lg bg-white/5 border border-glass-border">
                    <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Weekly Drawdown</div>
                    <div className={cn(
                        "text-lg font-bold font-mono",
                        Math.abs(drawdown.weekly_pct) > 5 ? "text-accent" : "text-white"
                    )}>
                        {(drawdown.weekly_pct ?? 0).toFixed(1)}%
                    </div>
                </div>
                <div className="p-3 rounded-lg bg-white/5 border border-glass-border">
                    <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Open Positions</div>
                    <div className="text-lg font-bold font-mono text-white">
                        {risk.open_positions ?? 0}/{risk.max_positions ?? 3}
                    </div>
                </div>
                <div className="p-3 rounded-lg bg-white/5 border border-glass-border">
                    <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Risk Budget</div>
                    <div className="text-lg font-bold font-mono text-primary">
                        ₹{(heat.remaining_budget || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                    </div>
                </div>
            </div>

            {/* Module Health */}
            {modules && (
                <div className="space-y-2">
                    <div className="flex items-center gap-2">
                        <Server className="h-3 w-3 text-gray-500" />
                        <span className="text-[10px] text-gray-500 uppercase tracking-wider">System Modules</span>
                    </div>
                    <div className="grid grid-cols-3 gap-1">
                        {Object.entries(modules.modules).map(([name, status]) => (
                            <div key={name} className="flex items-center gap-1.5 text-[10px]">
                                <span className={cn(
                                    "h-1.5 w-1.5 rounded-full flex-shrink-0",
                                    status.startsWith("✅") ? "bg-success" : "bg-accent"
                                )} />
                                <span className="text-gray-400 truncate">{name.replace(/_/g, " ")}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
