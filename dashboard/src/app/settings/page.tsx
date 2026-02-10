"use client";

import { useState, useEffect, useCallback } from "react";
import {
    Settings, Shield, Zap, Target, BarChart3, Bell, Brain, DollarSign,
    Search, Save, RefreshCw, Check, AlertTriangle, ToggleLeft, ToggleRight
} from "lucide-react";
import { cn } from "@/lib/utils";

const API_BASE = "http://localhost:8000";

// Section metadata for rendering
const SECTIONS: Record<string, { label: string; icon: any; description: string }> = {
    position_limits: { label: "Position Limits", icon: Shield, description: "Max positions, sizing, and portfolio risk" },
    entry_rules: { label: "Entry Rules", icon: Target, description: "Score thresholds, pullback, and volume rules" },
    exit_rules: { label: "Exit Rules", icon: Zap, description: "Stops, trailing, R:R, and hold time" },
    risk_management: { label: "Risk Management", icon: AlertTriangle, description: "Loss limits, drawdown, and scaling" },
    scanning: { label: "Scanner Config", icon: Search, description: "Scan intervals, price, and volume filters" },
    technical_criteria: { label: "Technical Weights", icon: BarChart3, description: "Indicator scoring weights (must sum to 100)" },
    alerts: { label: "Alerts", icon: Bell, description: "Notifications and alert thresholds" },
    learning: { label: "Learning Engine", icon: Brain, description: "Adaptive scoring and pattern tracking" },
    cost_optimization: { label: "Cost Optimization", icon: DollarSign, description: "Charges, DP fees, and batching" },
};

// Field display labels
const FIELD_LABELS: Record<string, string> = {
    max_positions: "Max Simultaneous Positions",
    max_trades_per_stock_per_day: "Max Trades / Stock / Day",
    max_daily_trades: "Max Daily Trades",
    position_size: "Position Size (₹)",
    max_portfolio_risk: "Max Portfolio Risk",
    min_capital_buffer: "Min Capital Buffer (₹)",
    dynamic_position_sizing: "Dynamic Position Sizing",
    minimum_score: "Minimum Entry Score",
    require_pullback: "Require Pullback",
    require_volume_confirmation: "Require Volume Confirm",
    avoid_gap_chase: "Avoid Gap Chase",
    min_atr_percentage: "Min ATR %",
    max_atr_percentage: "Max ATR %",
    use_dynamic_stops: "Dynamic Stop-Loss",
    use_trailing_stops: "Trailing Stops",
    risk_reward_minimum: "Min Risk:Reward",
    partial_exit_at_target1: "Partial Exit at T1",
    breakeven_after_target1: "Breakeven After T1",
    max_hold_time_hours: "Max Hold Time (hours)",
    pattern_invalidation_exit: "Pattern Invalidation Exit",
    market_close_time: "Market Close Time",
    force_exit_before_close: "Force Exit Before Close",
    single_exit_preferred: "Single Exit Preferred",
    max_loss_per_trade_percent: "Max Loss/Trade %",
    max_daily_loss_percent: "Max Daily Loss %",
    consecutive_losses_pause: "Pause After N Losses",
    scale_down_after_loss: "Scale Down After Loss",
    scale_up_after_win: "Scale Up After Win",
    check_capital_before_entry: "Check Capital Before Entry",
    min_balance_to_trade: "Min Balance to Trade (₹)",
    max_drawdown_daily: "Max Daily Drawdown (₹)",
    scan_interval_minutes: "Scan Interval (min)",
    min_volume: "Min Volume",
    min_price: "Min Price (₹)",
    max_price: "Max Price (₹)",
    support_resistance_weight: "S/R Weight",
    fair_value_gap_weight: "FVG Weight",
    trend_alignment_weight: "Trend Weight",
    candlestick_pattern_weight: "Pattern Weight",
    volume_profile_weight: "Volume Weight",
    risk_reward_weight: "R:R Weight",
    send_desktop_notification: "Desktop Notifications",
    send_to_journal: "Log to Journal",
    alert_on_score_above: "Alert Score Threshold",
    alert_on_exit_signal: "Alert on Exit Signal",
    alert_on_stop_approach: "Alert on Stop Approach",
    capture_all_signals: "Capture All Signals",
    capture_missed_opportunities: "Capture Missed Opps",
    daily_performance_analysis: "Daily Performance",
    pattern_success_tracking: "Pattern Tracking",
    adaptive_scoring: "Adaptive Scoring",
    min_profit_to_cover_charges: "Min Profit to Cover (₹)",
    charges_per_roundtrip: "Charges/Roundtrip (₹)",
    dp_charge_per_sell: "DP Charge/Sell (₹)",
    avoid_multiple_exits: "Avoid Multiple Exits",
    batch_exit_threshold: "Batch Exit Threshold %",
    track_costs_realtime: "Track Costs Real-time",
};

export default function SettingsPage() {
    const [config, setConfig] = useState<Record<string, any> | null>(null);
    const [originalConfig, setOriginalConfig] = useState<Record<string, any> | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [expandedSection, setExpandedSection] = useState<string | null>("position_limits");

    const fetchConfig = useCallback(async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/config`);
            if (res.ok) {
                const data = await res.json();
                setConfig(data.config);
                setOriginalConfig(JSON.parse(JSON.stringify(data.config)));
                setError(null);
            }
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchConfig(); }, [fetchConfig]);

    const handleSave = async () => {
        if (!config) return;
        setSaving(true);
        setSaved(false);
        try {
            const res = await fetch(`${API_BASE}/config`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ config }),
            });
            if (res.ok) {
                const data = await res.json();
                setOriginalConfig(JSON.parse(JSON.stringify(data.config)));
                setSaved(true);
                setTimeout(() => setSaved(false), 3000);
            }
        } catch (e: any) {
            setError(e.message);
        } finally {
            setSaving(false);
        }
    };

    const handleReset = () => {
        if (originalConfig) setConfig(JSON.parse(JSON.stringify(originalConfig)));
    };

    const updateField = (section: string, key: string, value: any) => {
        if (!config) return;
        setConfig({
            ...config,
            [section]: { ...config[section], [key]: value },
        });
    };

    const hasChanges = JSON.stringify(config) !== JSON.stringify(originalConfig);

    const renderField = (section: string, key: string, value: any) => {
        const label = FIELD_LABELS[key] || key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

        if (typeof value === "boolean") {
            const isOn = value;
            return (
                <div key={key} className="flex items-center justify-between py-2.5 px-1 border-b border-glass-border/30 last:border-0">
                    <span className="text-sm text-gray-300">{label}</span>
                    <button
                        onClick={() => updateField(section, key, !value)}
                        className="flex items-center gap-1.5"
                    >
                        {isOn ? (
                            <ToggleRight className="h-6 w-6 text-primary" />
                        ) : (
                            <ToggleLeft className="h-6 w-6 text-gray-600" />
                        )}
                    </button>
                </div>
            );
        }

        if (typeof value === "number") {
            return (
                <div key={key} className="flex items-center justify-between py-2.5 px-1 border-b border-glass-border/30 last:border-0">
                    <span className="text-sm text-gray-300">{label}</span>
                    <input
                        type="number"
                        value={value}
                        onChange={(e) => updateField(section, key, parseFloat(e.target.value) || 0)}
                        className="w-24 bg-black/30 border border-glass-border rounded-lg px-3 py-1.5 text-sm text-white text-right font-mono focus:outline-none focus:border-primary/50"
                    />
                </div>
            );
        }

        if (typeof value === "string") {
            return (
                <div key={key} className="flex items-center justify-between py-2.5 px-1 border-b border-glass-border/30 last:border-0">
                    <span className="text-sm text-gray-300">{label}</span>
                    <input
                        type="text"
                        value={value}
                        onChange={(e) => updateField(section, key, e.target.value)}
                        className="w-32 bg-black/30 border border-glass-border rounded-lg px-3 py-1.5 text-sm text-white text-right font-mono focus:outline-none focus:border-primary/50"
                    />
                </div>
            );
        }

        // Arrays and other types: show as read-only JSON
        if (Array.isArray(value)) {
            return (
                <div key={key} className="flex items-center justify-between py-2.5 px-1 border-b border-glass-border/30 last:border-0">
                    <span className="text-sm text-gray-300">{label}</span>
                    <span className="text-xs text-gray-500 font-mono">{JSON.stringify(value)}</span>
                </div>
            );
        }

        return null;
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <RefreshCw className="h-6 w-6 text-primary animate-spin" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                        <Settings className="h-6 w-6 text-primary" />
                        System Configuration
                    </h1>
                    <p className="text-sm text-gray-400 mt-1">
                        Edit trading_rules.json — changes apply immediately on save
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    {hasChanges && (
                        <button
                            onClick={handleReset}
                            className="px-3 py-1.5 rounded-lg bg-white/5 border border-glass-border text-gray-400 hover:text-white text-xs font-medium transition-all"
                        >
                            Discard
                        </button>
                    )}
                    <button
                        onClick={handleSave}
                        disabled={saving || !hasChanges}
                        className={cn(
                            "flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all",
                            hasChanges
                                ? "bg-primary text-black hover:bg-primary/90 shadow-[0_0_20px_rgba(6,182,212,0.3)]"
                                : saved
                                    ? "bg-success/20 text-success border border-success/30"
                                    : "bg-white/5 text-gray-500 border border-glass-border cursor-not-allowed"
                        )}
                    >
                        {saving ? <RefreshCw className="h-4 w-4 animate-spin" /> : saved ? <Check className="h-4 w-4" /> : <Save className="h-4 w-4" />}
                        {saving ? "Saving..." : saved ? "Saved!" : "Save Changes"}
                    </button>
                </div>
            </div>

            {error && (
                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                    ⚠️ {error}
                </div>
            )}

            {/* Top-level fields */}
            {config && (
                <div className="flex gap-3">
                    <div className="flex items-center gap-2 px-4 py-2 rounded-xl border border-glass-border bg-glass">
                        <span className="text-xs text-gray-500">Version</span>
                        <span className="text-sm font-mono text-white">{config.system_version}</span>
                    </div>
                    <div className="flex items-center gap-2 px-4 py-2 rounded-xl border border-glass-border bg-glass">
                        <span className="text-xs text-gray-500">Mode</span>
                        <select
                            value={config.mode || "hybrid"}
                            onChange={(e) => setConfig({ ...config, mode: e.target.value })}
                            className="bg-transparent text-sm text-primary font-medium focus:outline-none cursor-pointer"
                        >
                            <option value="hybrid">Hybrid</option>
                            <option value="cash">Cash Only</option>
                            <option value="options">Options Only</option>
                        </select>
                    </div>
                    <div className="flex items-center gap-2 px-4 py-2 rounded-xl border border-glass-border bg-glass">
                        <span className="text-xs text-gray-500">Auto Execute</span>
                        <button onClick={() => setConfig({ ...config, auto_execute: !config.auto_execute })}>
                            {config.auto_execute ? (
                                <ToggleRight className="h-5 w-5 text-primary" />
                            ) : (
                                <ToggleLeft className="h-5 w-5 text-gray-600" />
                            )}
                        </button>
                    </div>
                </div>
            )}

            {/* Config Sections */}
            {config && (
                <div className="space-y-3">
                    {Object.entries(SECTIONS).map(([sectionKey, meta]) => {
                        const sectionData = config[sectionKey];
                        if (!sectionData || typeof sectionData !== "object") return null;
                        const Icon = meta.icon;
                        const isExpanded = expandedSection === sectionKey;

                        return (
                            <div key={sectionKey} className="rounded-xl border border-glass-border bg-glass overflow-hidden">
                                <button
                                    onClick={() => setExpandedSection(isExpanded ? null : sectionKey)}
                                    className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors"
                                >
                                    <div className="flex items-center gap-3">
                                        <div className="h-9 w-9 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                                            <Icon className="h-4 w-4" />
                                        </div>
                                        <div className="text-left">
                                            <h3 className="text-sm font-semibold text-white">{meta.label}</h3>
                                            <p className="text-[11px] text-gray-500">{meta.description}</p>
                                        </div>
                                    </div>
                                    <div className={cn(
                                        "text-gray-500 transition-transform",
                                        isExpanded && "rotate-180"
                                    )}>
                                        ▾
                                    </div>
                                </button>

                                {isExpanded && (
                                    <div className="px-5 pb-4 border-t border-glass-border/50">
                                        {Object.entries(sectionData).map(([key, value]) =>
                                            renderField(sectionKey, key, value)
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
