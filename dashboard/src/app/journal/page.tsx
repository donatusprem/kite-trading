"use client";

import { useMemo } from "react";
import {
    BookOpen, BarChart3, TrendingUp, TrendingDown, Clock, Target, Zap,
    RefreshCw, Award, Activity, Calendar, ArrowUpRight, ArrowDownRight
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useJournalData } from "@/hooks/useJournalData";

export default function JournalPage() {
    const { trades, summary, activity, loading, error, refresh } = useJournalData();

    const closedTrades = useMemo(() => trades.filter((t) => t.status === "CLOSED"), [trades]);
    const openTrades = useMemo(() => trades.filter((t) => t.status === "OPEN"), [trades]);

    // Activity heatmap: last 90 days
    const heatmapDays = useMemo(() => {
        const days: { date: string; scans: number; trades: number; total: number }[] = [];
        const now = new Date();
        for (let i = 89; i >= 0; i--) {
            const d = new Date(now);
            d.setDate(d.getDate() - i);
            const key = d.toISOString().slice(0, 10);
            const act = activity[key];
            days.push({
                date: key,
                scans: act?.scans ?? 0,
                trades: act?.trades ?? 0,
                total: (act?.scans ?? 0) + (act?.trades ?? 0),
            });
        }
        return days;
    }, [activity]);

    const maxActivity = Math.max(...heatmapDays.map((d) => d.total), 1);

    // Exit type breakdown
    const exitTypes = summary?.exit_types ?? {};
    const totalExits = Object.values(exitTypes).reduce((a, b) => a + b, 0) || 1;

    const statCards = [
        {
            label: "Total Trades",
            value: summary?.total_trades ?? closedTrades.length,
            icon: BarChart3,
            color: "text-primary",
        },
        {
            label: "Win Rate",
            value: summary?.win_rate ? `${summary.win_rate.toFixed(1)}%` : `${closedTrades.length > 0 ? ((closedTrades.filter(t => t.pnl > 0).length / closedTrades.length) * 100).toFixed(1) : 0}%`,
            icon: Award,
            color: "text-yellow-500",
        },
        {
            label: "Total P&L",
            value: `₹${(summary?.total_pnl ?? closedTrades.reduce((a, t) => a + (t.pnl || 0), 0)).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`,
            icon: summary && summary.total_pnl >= 0 ? TrendingUp : TrendingDown,
            color: summary && summary.total_pnl >= 0 ? "text-success" : "text-red-400",
        },
        {
            label: "Avg R-Multiple",
            value: summary?.avg_r_multiple?.toFixed(2) ?? "--",
            icon: Target,
            color: "text-primary",
        },
        {
            label: "Avg Hold Time",
            value: summary?.avg_hold_time_minutes
                ? summary.avg_hold_time_minutes > 60
                    ? `${(summary.avg_hold_time_minutes / 60).toFixed(1)}h`
                    : `${summary.avg_hold_time_minutes.toFixed(0)}m`
                : "--",
            icon: Clock,
            color: "text-gray-300",
        },
    ];

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                        <BookOpen className="h-6 w-6 text-primary" />
                        Trading Journal
                    </h1>
                    <p className="text-sm text-gray-400 mt-1">
                        Performance metrics, trade history, and activity log
                    </p>
                </div>
                <button
                    onClick={() => refresh()}
                    disabled={loading}
                    className="p-2 rounded-lg bg-white/5 border border-glass-border text-gray-400 hover:text-white transition-all"
                >
                    <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
                </button>
            </div>

            {/* Stat Cards */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {statCards.map((card) => {
                    const Icon = card.icon;
                    return (
                        <div key={card.label} className="p-4 rounded-xl border border-glass-border bg-glass">
                            <div className="flex items-center gap-2 mb-2">
                                <Icon className={cn("h-4 w-4", card.color)} />
                                <span className="text-[11px] text-gray-500 uppercase tracking-wider">{card.label}</span>
                            </div>
                            <p className={cn("text-xl font-bold", card.color)}>{card.value}</p>
                        </div>
                    );
                })}
            </div>

            {/* Activity Heatmap */}
            <div className="p-5 rounded-xl border border-glass-border bg-glass">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-medium text-white flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-primary" />
                        Activity — Last 90 Days
                    </h3>
                    <div className="flex items-center gap-2 text-[10px] text-gray-500">
                        <span>Less</span>
                        {[0, 0.25, 0.5, 0.75, 1].map((level, i) => (
                            <div
                                key={i}
                                className="h-3 w-3 rounded-sm"
                                style={{
                                    backgroundColor: level === 0 ? "rgba(255,255,255,0.05)" : `rgba(6,182,212,${level * 0.8 + 0.2})`,
                                }}
                            />
                        ))}
                        <span>More</span>
                    </div>
                </div>
                <div className="flex flex-wrap gap-[3px]">
                    {heatmapDays.map((day) => {
                        const intensity = day.total > 0 ? Math.min(day.total / maxActivity, 1) : 0;
                        return (
                            <div
                                key={day.date}
                                className="h-3 w-3 rounded-sm cursor-default group relative"
                                style={{
                                    backgroundColor: intensity === 0
                                        ? "rgba(255,255,255,0.05)"
                                        : `rgba(6,182,212,${intensity * 0.8 + 0.2})`,
                                }}
                                title={`${day.date}: ${day.scans} scans, ${day.trades} trades`}
                            />
                        );
                    })}
                </div>
                <div className="flex gap-4 mt-3 text-[11px] text-gray-500">
                    <span>📊 {Object.values(activity).reduce((a, d) => a + d.scans, 0)} total scans</span>
                    <span>📈 {Object.values(activity).reduce((a, d) => a + d.trades, 0)} total trades</span>
                    <span>📅 {Object.keys(activity).length} active days</span>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Exit Type Breakdown */}
                <div className="p-5 rounded-xl border border-glass-border bg-glass">
                    <h3 className="text-sm font-medium text-white mb-4 flex items-center gap-2">
                        <Zap className="h-4 w-4 text-primary" />
                        Exit Type Breakdown
                    </h3>
                    {Object.keys(exitTypes).length > 0 ? (
                        <div className="space-y-3">
                            {Object.entries(exitTypes).map(([type, count]) => {
                                const pct = ((count as number) / totalExits) * 100;
                                const colors: Record<string, string> = {
                                    stop: "bg-red-500",
                                    target1: "bg-success",
                                    target2: "bg-primary",
                                    time: "bg-yellow-500",
                                    pattern_invalid: "bg-gray-500",
                                };
                                return (
                                    <div key={type}>
                                        <div className="flex justify-between text-xs mb-1">
                                            <span className="text-gray-400 capitalize">{type.replace("_", " ")}</span>
                                            <span className="text-white font-mono">{count as number} ({pct.toFixed(0)}%)</span>
                                        </div>
                                        <div className="h-1.5 w-full bg-gray-700 rounded-full overflow-hidden">
                                            <div
                                                className={cn("h-full rounded-full", colors[type] || "bg-primary")}
                                                style={{ width: `${pct}%` }}
                                            />
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-500 text-xs">
                            No closed trades yet — exit data will appear here
                        </div>
                    )}
                </div>

                {/* Quick Stats */}
                <div className="col-span-2 p-5 rounded-xl border border-glass-border bg-glass">
                    <h3 className="text-sm font-medium text-white mb-4 flex items-center gap-2">
                        <Activity className="h-4 w-4 text-primary" />
                        Trade Insights
                    </h3>
                    {summary && summary.total_trades > 0 ? (
                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-3 rounded-lg bg-white/5">
                                <span className="text-[11px] text-gray-500 block">Best Trade</span>
                                <span className="text-lg font-bold text-success">
                                    ₹{Math.max(...closedTrades.map((t) => t.pnl || 0), 0).toLocaleString()}
                                </span>
                            </div>
                            <div className="p-3 rounded-lg bg-white/5">
                                <span className="text-[11px] text-gray-500 block">Worst Trade</span>
                                <span className="text-lg font-bold text-red-400">
                                    ₹{Math.min(...closedTrades.map((t) => t.pnl || 0), 0).toLocaleString()}
                                </span>
                            </div>
                            <div className="p-3 rounded-lg bg-white/5">
                                <span className="text-[11px] text-gray-500 block">Avg P&L / Trade</span>
                                <span className="text-lg font-bold text-white">
                                    ₹{(summary.avg_pnl_per_trade || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                                </span>
                            </div>
                            <div className="p-3 rounded-lg bg-white/5">
                                <span className="text-[11px] text-gray-500 block">Profit Factor</span>
                                <span className="text-lg font-bold text-primary">
                                    {closedTrades.length > 0
                                        ? (() => {
                                            const gross = closedTrades.filter(t => t.pnl > 0).reduce((a, t) => a + t.pnl, 0);
                                            const loss = Math.abs(closedTrades.filter(t => t.pnl < 0).reduce((a, t) => a + t.pnl, 0));
                                            return loss > 0 ? (gross / loss).toFixed(2) : "∞";
                                        })()
                                        : "--"
                                    }
                                </span>
                            </div>
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-500 text-xs">
                            Start trading to see insights here
                        </div>
                    )}
                </div>
            </div>

            {/* Trade History Table */}
            <div className="rounded-xl border border-glass-border bg-glass overflow-hidden">
                <div className="p-5 border-b border-glass-border">
                    <h3 className="text-sm font-medium text-white flex items-center gap-2">
                        📋 Trade History
                        {closedTrades.length > 0 && (
                            <span className="text-xs text-gray-500 font-normal">({closedTrades.length} trades)</span>
                        )}
                    </h3>
                </div>

                {closedTrades.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="text-[11px] text-gray-500 uppercase tracking-wider border-b border-glass-border">
                                    <th className="py-3 px-4 text-left">Symbol</th>
                                    <th className="py-3 px-4 text-left">Setup</th>
                                    <th className="py-3 px-4 text-right">Entry</th>
                                    <th className="py-3 px-4 text-right">Exit</th>
                                    <th className="py-3 px-4 text-right">P&L</th>
                                    <th className="py-3 px-4 text-right">R</th>
                                    <th className="py-3 px-4 text-right">Hold</th>
                                    <th className="py-3 px-4 text-left">Exit Type</th>
                                    <th className="py-3 px-4 text-left">Date</th>
                                </tr>
                            </thead>
                            <tbody>
                                {closedTrades.slice().reverse().map((trade) => (
                                    <tr key={trade.trade_id} className="border-b border-glass-border/50 hover:bg-white/5 transition-colors">
                                        <td className="py-3 px-4 font-bold text-white">{trade.symbol}</td>
                                        <td className="py-3 px-4 text-gray-400 text-xs">{trade.setup_type || trade.entry_reason || "--"}</td>
                                        <td className="py-3 px-4 text-right font-mono text-gray-300">₹{trade.entry_price}</td>
                                        <td className="py-3 px-4 text-right font-mono text-gray-300">₹{trade.exit_price ?? "--"}</td>
                                        <td className={cn("py-3 px-4 text-right font-mono font-bold", trade.pnl >= 0 ? "text-success" : "text-red-400")}>
                                            <div className="flex items-center justify-end gap-1">
                                                {trade.pnl >= 0 ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                                                ₹{Math.abs(trade.pnl).toLocaleString()}
                                            </div>
                                        </td>
                                        <td className={cn("py-3 px-4 text-right font-mono text-xs", trade.r_multiple >= 0 ? "text-success" : "text-red-400")}>
                                            {trade.r_multiple?.toFixed(1) ?? "--"}R
                                        </td>
                                        <td className="py-3 px-4 text-right text-gray-400 text-xs">
                                            {trade.hold_time_minutes > 60
                                                ? `${(trade.hold_time_minutes / 60).toFixed(1)}h`
                                                : `${trade.hold_time_minutes}m`
                                            }
                                        </td>
                                        <td className="py-3 px-4">
                                            <span className={cn(
                                                "text-[10px] px-2 py-0.5 rounded font-medium",
                                                trade.exit_type === "target1" || trade.exit_type === "target2" ? "bg-success/10 text-success" :
                                                    trade.exit_type === "stop" ? "bg-red-500/10 text-red-400" :
                                                        "bg-gray-500/10 text-gray-400"
                                            )}>
                                                {trade.exit_type?.toUpperCase() || "--"}
                                            </span>
                                        </td>
                                        <td className="py-3 px-4 text-gray-500 text-xs">
                                            {trade.entry_time ? new Date(trade.entry_time).toLocaleDateString() : "--"}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center py-16 text-gray-500">
                        <BookOpen className="h-12 w-12 mb-4 opacity-30" />
                        <h3 className="text-lg font-medium text-white mb-1">No Trade History Yet</h3>
                        <p className="text-sm max-w-sm text-center">
                            Trades will appear here once the execution engine places orders. Scan activity is tracked in the heatmap above.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
