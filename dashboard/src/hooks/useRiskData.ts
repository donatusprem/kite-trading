"use client";

import { useState, useEffect } from "react";
import { fetchApi, type RiskDashboard, type ModuleStatus } from "@/lib/api";

export function useRiskData() {
    const [risk, setRisk] = useState<RiskDashboard | null>(null);
    const [modules, setModules] = useState<ModuleStatus | null>(null);

    useEffect(() => {
        const fetchRisk = async () => {
            const [riskData, moduleData] = await Promise.all([
                fetchApi<RiskDashboard>("/risk/dashboard"),
                fetchApi<ModuleStatus>("/system/modules"),
            ]);
            if (riskData) setRisk(riskData);
            if (moduleData) setModules(moduleData);
        };

        fetchRisk();
        const interval = setInterval(fetchRisk, 15000);
        return () => clearInterval(interval);
    }, []);

    return { risk, modules };
}
