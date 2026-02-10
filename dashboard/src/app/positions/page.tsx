"use client";

import React from "react";
import { LineChart, ArrowUpRight, ArrowDownRight, RefreshCw } from "lucide-react";
import { useSystemData } from "@/hooks/useSystemData";

export default function PositionsPage() {
    const { positions, marketStatus, isConnected } = useSystemData();

    const totalPnL = positions.reduce((acc, p) => acc + (p.pnl || 0), 0);

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-start">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                        <LineChart className="h-6 w-6 text-primary" />
                        Active Positions
                    </h1>
                    <p className="text-gray-400 mt-1">
                        Real-time tracking of open trades.
                    </p>
                </div>
                <div className="text-right">
                    <div className="text-sm text-gray-400">Total P&L</div>
                    <div className={`text-2xl font-bold ${totalPnL >= 0 ? 'text-success' : 'text-error'}`}>
                        {(totalPnL ?? 0) >= 0 ? '+' : ''}₹{(totalPnL ?? 0).toLocaleString()}
                    </div>
                </div>
            </div>

            {!isConnected && (
                <div className="p-4 rounded-lg bg-orange-500/10 border border-orange-500/20 text-orange-400 flex items-center gap-2">
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Connecting to Live Feed...
                </div>
            )}

            {positions.length === 0 ? (
                <div className="p-12 rounded-xl border border-glass-border bg-glass/20 flex flex-col items-center justify-center text-center space-y-4">
                    <div className="h-16 w-16 rounded-full bg-white/5 flex items-center justify-center">
                        <LineChart className="h-8 w-8 text-gray-500" />
                    </div>
                    <div>
                        <h3 className="text-lg font-medium text-white">No Active Positions</h3>
                        <p className="text-gray-500 max-w-sm">
                            Market scan is running. New positions will appear here automatically.
                        </p>
                    </div>
                </div>
            ) : (
                <div className="grid gap-4">
                    {positions.map((pos, idx) => (
                        <div key={idx} className="p-6 rounded-xl border border-glass-border bg-glass/30 hover:bg-glass/40 transition-colors">
                            <div className="flex justify-between items-start">
                                <div>
                                    <div className="flex items-center gap-2">
                                        <h3 className="text-lg font-bold text-white">{pos.symbol}</h3>
                                        <span className={`text-xs px-2 py-0.5 rounded ${pos.type === 'LONG' ? 'bg-success/20 text-success' : 'bg-error/20 text-error'}`}>
                                            {pos.type}
                                        </span>
                                    </div>
                                    <div className="flex gap-4 mt-2 text-sm text-gray-400">
                                        <span>Qty: {pos.quantity}</span>
                                        <span>Avg: ₹{pos.entry_price}</span>
                                        <span>LTP: ₹{pos.current_price}</span>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className={`text-xl font-bold ${pos.pnl >= 0 ? 'text-success' : 'text-error'}`}>
                                        {(pos.pnl ?? 0) >= 0 ? '+' : ''}₹{(pos.pnl ?? 0).toLocaleString()}
                                    </div>
                                    <div className={`text-sm ${pos.pnl >= 0 ? 'text-success/70' : 'text-error/70'}`}>
                                        {pos.pnl_percent}%
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
