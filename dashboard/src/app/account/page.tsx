"use client";

import { AccountOverview } from "@/components/AccountOverview";

export default function AccountPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Account Overview</h1>
        <p className="text-gray-400 mt-1">
          Real-time view of your Kite account, holdings, and backtest results
        </p>
      </div>

      <AccountOverview />
    </div>
  );
}
