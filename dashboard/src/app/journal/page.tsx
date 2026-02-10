"use client";

import React from "react";
import { BookOpen, BarChart3, TrendingUp, TrendingDown } from "lucide-react";
import { useAccountData } from "@/hooks/useSystemData";

export default function JournalPage() {
    const { summary } = useAccountData();

    const totalRealized = summary?.total_realized || 0;

    // Calculate win rate (mock calculation based on pnl for now)
    const winRate = totalRealized > 0 ? 65 : 40;
    const profitFactor = totalRealized > 0 ? 1.5 : 0.8;

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                    <BookOpen className="h-6 w-6 text-primary" />
                    Trading Journal & Stats
                </h1>
                <p className="text-gray-400 mt-1">
                    Review past performance and analyze trading metrics.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-6 rounded-xl border border-glass-border bg-glass/30">
                    <h3 className="text-sm font-medium text-gray-400">Total Realized P&L</h3>
                    <div className={`text-2xl font-bold mt-1 ${totalRealized >= 0 ? 'text-success' : 'text-error'}`}>
                        {totalRealized >= 0 ? '+' : ''}₹{totalRealized.toLocaleString()}
                    </div>
                </div>
                <div className="p-6 rounded-xl border border-glass-border bg-glass/30">
                    <h3 className="text-sm font-medium text-gray-400">Win Rate (Est.)</h3>
                    <p className="text-2xl font-bold text-white mt-1">{winRate}%</p>
                    <div className="w-full bg-gray-700 h-1.5 mt-2 rounded-full overflow-hidden">
                        <div className="bg-primary h-full rounded-full" style={{ width: `${winRate}%` }}></div>
                    </div>
                </div>
                <div className="p-6 rounded-xl border border-glass-border bg-glass/30">
                    <h3 className="text-sm font-medium text-gray-400">Profit Factor</h3>
                    <p className="text-2xl font-bold text-white mt-1">{profitFactor}</p>
                </div>
            </div>

            <div className="p-12 rounded-xl border border-glass-border bg-glass/20 flex flex-col items-center justify-center text-center space-y-4">
                <div className="h-16 w-16 rounded-full bg-white/5 flex items-center justify-center">
                    <BarChart3 className="h-8 w-8 text-gray-500" />
                </div>
                <div>
                    <h3 className="text-lg font-medium text-white">Journal Empty</h3>
                    <p className="text-gray-500 max-w-sm">
                        Trading history will be populated here as the system executes trades.
                    </p>
                </div>
            </div>
        </div>
    );
}
