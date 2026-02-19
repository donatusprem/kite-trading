"use client";

import { Activity, ArrowUpRight, ArrowDownRight, Zap, Target, TrendingUp, AlertTriangle, BarChart3, RefreshCw, Radio } from "lucide-react";
import { cn } from "@/lib/utils";
import { useSystemData } from "@/hooks/useSystemData";
import { useRiskData } from "@/hooks/useRiskData";
import { useTickerWebSocket } from "@/hooks/useTickerWebSocket";
import { RiskDashboardPanel } from "@/components/RiskDashboard";
import Link from "next/link";

export default function Home() {
  const { marketStatus, positions, latestScan, isConnected, isScanning, triggerLiveScan } = useSystemData();
  const { risk, modules } = useRiskData();
  const { ticks, isConnected: isTickerLive, instrumentCount, getPrice } = useTickerWebSocket();

  // All derived from live API data - no hardcoded values
  const activePositionsCount = positions.length;
  const sentimentScore = marketStatus?.sentiment_score ?? 0;
  const sessionPnl = marketStatus?.session_pnl ?? 0;
  const totalRealized = marketStatus?.total_realized ?? 0;
  // Calculate win rate from positions: closed positions with profit / total closed
  const closedPositions = positions.filter((p: any) => p.type === "closed");
  const winningTrades = closedPositions.filter((p: any) => p.pnl > 0);
  const winRate = closedPositions.length > 0
    ? Math.round((winningTrades.length / closedPositions.length) * 100)
    : 0;

  const opportunities = Array.isArray(latestScan?.data) ? latestScan.data : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight text-white">Command Center</h1>
        <div className="flex items-center gap-3 text-sm">
          {isTickerLive && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-success/10 border border-success/20">
              <Radio className="h-3 w-3 text-success animate-pulse" />
              <span className="text-success text-xs font-semibold">LIVE</span>
              <span className="text-gray-500 text-[10px]">{instrumentCount} ticks</span>
            </div>
          )}
          {isConnected ? (
            <>
              <span className="h-2 w-2 rounded-full bg-success animate-pulse"></span>
              <span className="text-gray-400">System Online</span>
            </>
          ) : (
            <>
              <span className="h-2 w-2 rounded-full bg-accent animate-pulse"></span>
              <span className="text-accent">Connecting...</span>
            </>
          )}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Sentiment Card */}
        <div className="relative overflow-hidden rounded-xl border border-glass-border bg-glass p-5 transition-all hover:border-primary/30 group">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-400">AI Sentiment</p>
              <div className="mt-2 flex items-baseline gap-2">
                <span className={cn("text-2xl font-bold", sentimentScore > 60 ? "text-success" : sentimentScore < 40 ? "text-accent" : "text-yellow-500")}>
                  {sentimentScore}/100
                </span>
                <span className="text-xs font-medium text-gray-400">
                  {marketStatus?.trend || "Neutral"}
                </span>
              </div>
            </div>
            <div className="rounded-lg bg-white/5 p-2 text-primary">
              <Zap className="h-5 w-5" />
            </div>
          </div>
        </div>

        {/* Positions Card */}
        <div className="relative overflow-hidden rounded-xl border border-glass-border bg-glass p-5 transition-all hover:border-primary/30 group">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-400">Active Positions</p>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-white">{activePositionsCount}</span>
                <span className="text-xs font-medium text-success">Live</span>
              </div>
            </div>
            <div className="rounded-lg bg-white/5 p-2 text-primary">
              <Activity className="h-5 w-5" />
            </div>
          </div>
        </div>

        {/* Win Rate - from live closed trades */}
        <div className="relative overflow-hidden rounded-xl border border-glass-border bg-glass p-5 transition-all hover:border-primary/30 group">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-400">Win Rate</p>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-white">
                  {closedPositions.length > 0 ? `${winRate}%` : "--"}
                </span>
                <span className="text-xs font-medium text-gray-400">
                  {closedPositions.length > 0 ? `${winningTrades.length}/${closedPositions.length} trades` : "No closed trades"}
                </span>
              </div>
            </div>
            <div className="rounded-lg bg-white/5 p-2 text-primary">
              <Target className="h-5 w-5" />
            </div>
          </div>
        </div>

        {/* Session PnL - from live API */}
        <div className="relative overflow-hidden rounded-xl border border-glass-border bg-glass p-5 transition-all hover:border-primary/30 group">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-400">Session PnL</p>
              <div className="mt-2 flex items-baseline gap-2">
                <span className={cn("text-2xl font-bold", sessionPnl >= 0 ? "text-success" : "text-accent")}>
                  {isConnected && marketStatus?.is_live
                    ? `${(sessionPnl ?? 0) >= 0 ? "+" : ""}₹${(sessionPnl ?? 0).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`
                    : "--"}
                </span>
                {isConnected && marketStatus?.is_live && (
                  <span className={cn("text-xs font-medium flex items-center gap-0.5", sessionPnl >= 0 ? "text-success" : "text-accent")}>
                    {sessionPnl >= 0 ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                    {(totalRealized ?? 0) >= 0 ? "+" : ""}₹{(totalRealized ?? 0).toLocaleString("en-IN", { maximumFractionDigits: 0 })} realized
                  </span>
                )}
              </div>
            </div>
            <div className="rounded-lg bg-white/5 p-2 text-primary">
              <TrendingUp className="h-5 w-5" />
            </div>
          </div>
        </div>
      </div>

      {/* Quick Action */}
      <div className="flex gap-3">
        <Link href="/signals?symbol=NIFTY 50" className="flex-1 flex items-center justify-center gap-2 p-3 rounded-xl bg-primary/10 border border-primary/20 text-primary text-sm font-medium hover:bg-primary/20 transition-all hover:shadow-[0_0_15px_rgba(6,182,212,0.15)]">
          <BarChart3 className="h-4 w-4" />
          Deep Analysis
        </Link>
      </div>

      <div className="grid gap-6 md:grid-cols-7">
        {/* Main Chart / AI Insight Area */}
        <div className="col-span-4 rounded-xl border border-glass-border bg-glass p-6 min-h-[400px]">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-lg text-white">Latest AI Scans</h3>
            <div className="flex items-center gap-2">
              <button
                onClick={() => triggerLiveScan()}
                disabled={isScanning || !isConnected}
                className={cn(
                  "p-1.5 rounded-lg bg-white/5 border border-glass-border text-gray-400 hover:text-white transition-all",
                  (isScanning || !isConnected) && "opacity-50 cursor-not-allowed"
                )}
              >
                <RefreshCw className={cn("h-3.5 w-3.5", isScanning && "animate-spin")} />
              </button>
              <Link href="/scanner" className="text-xs text-primary hover:text-primary/80">View Full Scan &rarr;</Link>
            </div>
          </div>

          <div className="space-y-3">
            {!isConnected && (
              <div className="flex flex-col items-center justify-center py-10 text-gray-500 text-xs">
                <AlertTriangle className="h-6 w-6 mb-2 opacity-50 text-yellow-500" />
                Waiting for Backend Connection...
              </div>
            )}

            {opportunities.length === 0 && isConnected && (
              <div className="text-center py-10 text-gray-500 text-xs">
                No active high-confidence setups found yet.
              </div>
            )}

            {opportunities.map((op: any, i: number) => (
              <div
                key={i}
                onClick={() => window.location.href = `/signals?symbol=${op.symbol}`}
                className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-transparent hover:border-primary/30 hover:bg-white/10 transition-all cursor-pointer group"
              >
                <div className="flex items-center gap-4">
                  <div className={cn("flex h-10 w-10 items-center justify-center rounded-lg font-bold text-xs", (op.score || 0) > 80 ? "bg-success/20 text-success" : "bg-primary/20 text-primary")}>
                    {op.score || "?"}
                  </div>
                  <div>
                    <div className="font-bold text-white">{op.symbol}</div>
                    <div className="text-xs text-gray-400">{op.pattern || "Pattern Detected"}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-white font-mono">₹{op.ltp || op.price}</div>
                  <div className={cn("text-xs font-medium flex items-center justify-end gap-1", "text-success")}>
                    <ArrowUpRight className="h-3 w-3" />
                    Long
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Side Panel: Positions + Risk */}
        <div className="col-span-3 space-y-4">
          <div className="rounded-xl border border-glass-border bg-glass p-6">
            <h3 className="font-semibold text-lg text-white mb-4">Live Positions</h3>

            {activePositionsCount === 0 ? (
              <div className="flex flex-col items-center justify-center h-[200px] text-gray-500 text-sm border-2 border-dashed border-glass-border rounded-lg">
                <Activity className="h-8 w-8 mb-2 opacity-50" />
                No active positions
                <span className="text-xs opacity-50 mt-1">AI is scanning the market...</span>
              </div>
            ) : (
              <div className="space-y-4">
                {positions.map((pos: any, i: number) => {
                  // Use live tick price if available, else fall back to cached price
                  const tickData = getPrice(pos.symbol);
                  const livePrice = tickData?.ltp ?? pos.current_price ?? pos.last_price ?? 0;
                  const entryPrice = pos.entry_price ?? pos.average_price ?? 0;
                  const qty = pos.quantity ?? 0;
                  const livePnl = tickData ? (livePrice - entryPrice) * qty : (pos.pnl ?? 0);
                  const livePnlPct = entryPrice > 0 ? ((livePrice - entryPrice) / entryPrice) * 100 : (pos.pnl_pct ?? 0);
                  const isProfit = livePnl >= 0;
                  const isShort = qty < 0;
                  const isClosed = pos.type === "closed";
                  const progressWidth = Math.min(Math.abs(livePnlPct), 100);
                  const hasTick = !!tickData;

                  return (
                    <div key={i} className={cn(
                      "p-4 rounded-lg border",
                      isClosed ? "bg-white/3 border-glass-border opacity-70" : "bg-white/5 border-glass-border"
                    )}>
                      <div className="flex justify-between items-start mb-1">
                        <div>
                          <span className="font-bold text-white">{pos.symbol}</span>
                          <span className={cn(
                            "ml-2 text-[10px] px-1.5 py-0.5 rounded font-medium",
                            isShort ? "bg-accent/20 text-accent" : isClosed ? "bg-gray-500/20 text-gray-400" : "bg-success/20 text-success"
                          )}>
                            {isClosed ? "CLOSED" : isShort ? "SHORT" : "LONG"}
                          </span>
                          {hasTick && (
                            <span className="ml-1.5 text-[9px] px-1 py-0.5 rounded bg-cyan-500/10 text-cyan-400 font-mono">
                              LIVE
                            </span>
                          )}
                        </div>
                        <span className={cn("text-sm font-mono font-bold", isProfit ? "text-success" : "text-accent")}>
                          {isProfit ? "+" : ""}₹{(livePnl ?? 0).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                        </span>
                      </div>
                      <div className="flex justify-between items-center text-xs text-gray-400 mb-2">
                        <span>
                          {qty !== 0 ? `${Math.abs(qty)} qty @ ₹${entryPrice}` : `Sold @ ₹${pos.sell_price || entryPrice}`}
                          {hasTick && <span className="ml-1 text-cyan-400">→ ₹{livePrice.toLocaleString("en-IN", { maximumFractionDigits: 2 })}</span>}
                        </span>
                        <span className={cn("font-medium", isProfit ? "text-success" : "text-accent")}>
                          {livePnlPct >= 0 ? "+" : ""}{livePnlPct.toFixed(1)}%
                        </span>
                      </div>
                      <div className="h-1.5 w-full bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className={cn("h-full rounded-full transition-all duration-300", isProfit ? "bg-success" : "bg-accent")}
                          style={{ width: `${progressWidth}%` }}
                        ></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Risk Widget */}
          <RiskDashboardPanel risk={risk} modules={modules} />
        </div>
      </div>
    </div>
  );
}
