"use client";

import React from "react";
import { Settings, Shield, Zap } from "lucide-react";

export default function SettingsPage() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                    <Settings className="h-6 w-6 text-primary" />
                    System Configuration
                </h1>
                <p className="text-gray-400 mt-1">
                    Manage system parameters, risk limits, and API connections.
                </p>
            </div>

            <div className="space-y-4">
                <div className="p-6 rounded-xl border border-glass-border bg-glass/30">
                    <div className="flex items-start justify-between">
                        <div className="flex gap-3">
                            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                                <Shield className="h-5 w-5" />
                            </div>
                            <div>
                                <h3 className="text-lg font-medium text-white">Risk Management</h3>
                                <p className="text-sm text-gray-400">Configure stop-loss, max daily loss, and position sizing.</p>
                            </div>
                        </div>
                        <button className="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-sm font-medium text-white transition-colors">
                            Configure
                        </button>
                    </div>
                </div>

                <div className="p-6 rounded-xl border border-glass-border bg-glass/30">
                    <div className="flex items-start justify-between">
                        <div className="flex gap-3">
                            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                                <Zap className="h-5 w-5" />
                            </div>
                            <div>
                                <h3 className="text-lg font-medium text-white">Trading Logic</h3>
                                <p className="text-sm text-gray-400">Adjust strategy parameters and indicators.</p>
                            </div>
                        </div>
                        <button className="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-sm font-medium text-white transition-colors">
                            Configure
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
