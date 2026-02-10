"use client";

import { Shield } from "lucide-react";
import { useRiskData } from "@/hooks/useRiskData";
import { RiskDashboardPanel } from "@/components/RiskDashboard";

export default function RiskPage() {
    const { risk, modules } = useRiskData();

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-white">Risk Manager</h1>
                    <p className="text-sm text-gray-400 mt-1">Portfolio heat • Drawdown breakers • Kelly sizing • Sector limits</p>
                </div>
                <div className="flex items-center gap-2">
                    <Shield className="h-4 w-4 text-primary" />
                    <span className="text-xs text-gray-400">Auto-refresh 15s</span>
                </div>
            </div>

            <div className="max-w-2xl">
                <RiskDashboardPanel risk={risk} modules={modules} />
            </div>
        </div>
    );
}
