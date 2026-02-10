"use client";

import { Wallet, TrendingDown, TrendingUp, PieChart } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAccountData } from "@/hooks/useSystemData";
import { formatINR, formatPercent, backtestResults } from "@/lib/kiteData";

export function AccountOverview() {
  const { margins, holdings, summary } = useAccountData();

  const netMargin = margins?.net ?? 0;
  const cashBalance = margins?.cash ?? 0;
  const collateral = margins?.collateral ?? 0;
  const optionPremiumUsed = margins?.option_premium_used ?? 0;

  const sessionPnl = summary?.session_pnl ?? 0;
  const totalRealized = summary?.total_realized ?? 0;
  const totalUnrealized = summary?.total_unrealized ?? 0;
  const activePositions = summary?.positions ?? [];
  const closedPositions = summary?.closed_positions ?? [];
  const totalPortfolio = netMargin + holdings.reduce((sum: number, h: any) => sum + (h.value || 0), 0);

  const utilizationPercent = optionPremiumUsed > 0 ? (optionPremiumUsed / netMargin) * 100 : 0;

  return (
    <div className="space-y-6">
      {/* Account Balance Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        {/* Available Margin */}
        <div className="rounded-xl border border-glass-border bg-glass p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-400">Available Margin</p>
              <div className="mt-2">
                <span className="text-2xl font-bold text-white">
                  {formatINR(netMargin)}
                </span>
                <p className="text-xs text-gray-500 mt-1">
                  Cash: {formatINR(cashBalance)} |
                  Collateral: {formatINR(collateral)}
                </p>
              </div>
            </div>
            <div className="rounded-lg bg-white/5 p-2 text-primary">
              <Wallet className="h-5 w-5" />
            </div>
          </div>
        </div>

        {/* Session P&L */}
        <div className="rounded-xl border border-glass-border bg-glass p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-400">Session P&L</p>
              <div className="mt-2">
                <span className={cn("text-2xl font-bold", sessionPnl >= 0 ? "text-success" : "text-accent")}>
                  {sessionPnl >= 0 ? "+" : ""}{formatINR(sessionPnl)}
                </span>
                <p className="text-xs text-gray-500 mt-1">
                  Realized: {formatINR(totalRealized)} |
                  Unrealized: {formatINR(totalUnrealized)}
                </p>
              </div>
            </div>
            <div className="rounded-lg bg-white/5 p-2 text-primary">
              {sessionPnl >= 0 ? <TrendingUp className="h-5 w-5" /> : <TrendingDown className="h-5 w-5" />}
            </div>
          </div>
        </div>

        {/* Total Portfolio */}
        <div className="rounded-xl border border-glass-border bg-glass p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-400">Total Portfolio</p>
              <div className="mt-2">
                <span className="text-2xl font-bold text-white">
                  {formatINR(totalPortfolio)}
                </span>
                <p className="text-xs text-gray-500 mt-1">
                  {activePositions.length} active | {closedPositions.length} closed today
                </p>
              </div>
            </div>
            <div className="rounded-lg bg-white/5 p-2 text-primary">
              <PieChart className="h-5 w-5" />
            </div>
          </div>
        </div>
      </div>

      {/* Active Positions */}
      {activePositions.length > 0 && (
        <div className="rounded-xl border border-glass-border bg-glass p-6">
          <h3 className="font-semibold text-lg text-white mb-4">Active Positions</h3>
          <div className="space-y-3">
            {activePositions.map((pos: any, i: number) => (
              <div key={i} className="p-4 rounded-lg bg-white/5 border border-glass-border">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <span className="font-bold text-white text-lg">{pos.symbol}</span>
                    <span className={cn(
                      "ml-2 text-xs px-2 py-0.5 rounded",
                      (pos.quantity ?? 0) < 0 ? "bg-accent/20 text-accent" : "bg-success/20 text-success"
                    )}>
                      {(pos.quantity ?? 0) < 0 ? "SHORT" : "LONG"} | {Math.abs(pos.quantity)} qty
                    </span>
                  </div>
                  <div className="text-right">
                    <span className={cn(
                      "text-lg font-bold font-mono",
                      (pos.pnl ?? 0) >= 0 ? "text-success" : "text-accent"
                    )}>
                      {(pos.pnl ?? 0) >= 0 ? "+" : ""}{formatINR(pos.pnl ?? 0)}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-400">
                  <span>Entry: {formatINR(pos.average_price)}</span>
                  <span>|</span>
                  <span>LTP: {formatINR(pos.last_price)}</span>
                  <span>|</span>
                  <span className={cn(
                    "font-medium",
                    (pos.pnl_pct ?? 0) >= 0 ? "text-success" : "text-accent"
                  )}>
                    {formatPercent(pos.pnl_pct ?? 0)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Closed Positions Today */}
      {closedPositions.length > 0 && (
        <div className="rounded-xl border border-glass-border bg-glass p-6">
          <h3 className="font-semibold text-lg text-white mb-4">Closed Today</h3>
          <div className="space-y-3">
            {closedPositions.map((pos: any, i: number) => (
              <div key={i} className="p-4 rounded-lg bg-white/5 border border-glass-border opacity-80">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <span className="font-bold text-white">{pos.symbol}</span>
                    <span className="ml-2 text-xs bg-gray-500/20 text-gray-400 px-2 py-0.5 rounded">CLOSED</span>
                  </div>
                  <span className={cn(
                    "text-lg font-bold font-mono",
                    (pos.pnl ?? 0) >= 0 ? "text-success" : "text-accent"
                  )}>
                    {(pos.pnl ?? 0) >= 0 ? "+" : ""}{formatINR(pos.pnl ?? 0)}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-400">
                  <span>Buy: {formatINR(pos.average_price)}</span>
                  <span>|</span>
                  <span>Sell: {formatINR(pos.sell_price || pos.last_price)}</span>
                  <span>|</span>
                  <span className={cn("font-medium", (pos.pnl_pct ?? 0) >= 0 ? "text-success" : "text-accent")}>
                    {formatPercent(pos.pnl_pct ?? 0)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Current Holdings */}
      <div className="rounded-xl border border-glass-border bg-glass p-6">
        <h3 className="font-semibold text-lg text-white mb-4">Current Holdings</h3>
        {holdings.length === 0 ? (
          <div className="text-center py-8 text-gray-500 text-sm">
            No holdings in portfolio
          </div>
        ) : (
          <div className="space-y-3">
            {holdings.map((holding: any, i: number) => (
              <div key={i} className="p-4 rounded-lg bg-white/5 border border-glass-border">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <span className="font-bold text-white text-lg">{holding.symbol}</span>
                    <p className="text-xs text-gray-400">
                      {holding.quantity} shares @ {formatINR(holding.avgPrice || holding.average_price)} avg
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-white font-mono text-lg">
                      {formatINR(holding.value)}
                    </span>
                    <p className={cn(
                      "text-sm font-medium flex items-center justify-end gap-1 mt-1",
                      (holding.pnl ?? 0) >= 0 ? "text-success" : "text-accent"
                    )}>
                      {(holding.pnl ?? 0) >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                      {formatPercent(holding.pnlPercent || holding.pnl_pct || 0)} ({formatINR(holding.pnl ?? 0)})
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Backtest Results Summary */}
      <div className="rounded-xl border border-glass-border bg-glass p-6">
        <h3 className="font-semibold text-lg text-white mb-4">
          Strategy Backtest Results
          <span className="text-xs text-gray-400 ml-2 font-normal">
            (Aug 2025 - Feb 2026)
          </span>
        </h3>

        <div className="space-y-3">
          {backtestResults.map((result, i) => (
            <div
              key={i}
              className={cn(
                "p-4 rounded-lg border",
                i === 0 && result.returnPercent > 0
                  ? "bg-success/10 border-success/30"
                  : "bg-white/5 border-glass-border"
              )}
            >
              <div className="flex items-center justify-between mb-2">
                <div>
                  <span className="font-bold text-white">{result.strategy}</span>
                  {i === 0 && result.returnPercent > 0 && (
                    <span className="ml-2 text-xs bg-success/20 text-success px-2 py-1 rounded">
                      BEST
                    </span>
                  )}
                </div>
                <span className={cn(
                  "text-lg font-bold",
                  result.returnPercent >= 0 ? "text-success" : "text-accent"
                )}>
                  {formatPercent(result.returnPercent)}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-4 text-xs">
                <div>
                  <p className="text-gray-400">Win Rate</p>
                  <p className="text-white font-medium">{result.winRate.toFixed(1)}%</p>
                </div>
                <div>
                  <p className="text-gray-400">Trades</p>
                  <p className="text-white font-medium">
                    {result.winners}W / {result.losers}L
                  </p>
                </div>
                <div>
                  <p className="text-gray-400">Profit</p>
                  <p className={cn(
                    "font-medium",
                    result.profitAmount >= 0 ? "text-success" : "text-accent"
                  )}>
                    {formatINR(result.profitAmount)}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Risk Management */}
      <div className="rounded-xl border border-glass-border bg-glass p-6">
        <h3 className="font-semibold text-lg text-white mb-4">Risk Management</h3>

        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-gray-400">Margin Utilization</span>
              <span className="text-white font-medium">
                {utilizationPercent.toFixed(1)}%
              </span>
            </div>
            <div className="h-2 w-full bg-gray-700 rounded-full overflow-hidden">
              <div
                className={cn(
                  "h-full transition-all",
                  utilizationPercent < 50 && "bg-success",
                  utilizationPercent >= 50 && utilizationPercent < 80 && "bg-yellow-500",
                  utilizationPercent >= 80 && "bg-accent"
                )}
                style={{ width: `${Math.min(utilizationPercent, 100)}%` }}
              ></div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="p-3 rounded-lg bg-white/5">
              <p className="text-gray-400 mb-1">Option Premium Used</p>
              <p className="text-white font-bold">{formatINR(optionPremiumUsed)}</p>
            </div>
            <div className="p-3 rounded-lg bg-white/5">
              <p className="text-gray-400 mb-1">Cash Available</p>
              <p className="text-white font-bold">{formatINR(cashBalance)}</p>
            </div>
          </div>

          {activePositions.length > 0 && (
            <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/30">
              <p className="text-sm text-blue-400 font-medium">
                {activePositions.length} active position(s) using {formatINR(optionPremiumUsed)} margin
              </p>
              <p className="text-xs text-gray-400 mt-1">
                Net margin available: {formatINR(netMargin)}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
