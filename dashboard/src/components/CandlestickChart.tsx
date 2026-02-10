"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import {
    createChart,
    ColorType,
    CrosshairMode,
    CandlestickSeries,
    HistogramSeries,
    LineSeries,
} from "lightweight-charts";
import type {
    IChartApi,
    ISeriesApi,
    CandlestickData,
    HistogramData,
    LineData,
} from "lightweight-charts";

interface ChartProps {
    symbol: string;
    onClose?: () => void;
}

interface AnalysisData {
    score: number;
    trend: { direction: string; strength: string };
    ema20: { time: string; value: number }[];
    ema50: { time: string; value: number }[];
    support: number[];
    resistance: number[];
    fvgs: { type: string; high: number; low: number }[];
    patterns: {
        time: string;
        position: string;
        color: string;
        shape: string;
        text: string;
    }[];
    setup_type: string;
}

export default function CandlestickChart({ symbol, onClose }: ChartProps) {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [analysis, setAnalysis] = useState<AnalysisData | null>(null);

    const fetchAndRender = useCallback(async () => {
        if (!chartContainerRef.current) return;

        setLoading(true);
        setError(null);

        try {
            // Fetch candle data and analysis in parallel
            const [chartRes, analysisRes] = await Promise.all([
                fetch(`http://localhost:8000/chart/${symbol}`),
                fetch(`http://localhost:8000/chart/${symbol}/analysis`),
            ]);

            if (!chartRes.ok) throw new Error(`No chart data for ${symbol}`);

            const chartData = await chartRes.json();
            const analysisData = analysisRes.ok ? await analysisRes.json() : null;

            if (analysisData && !analysisData.error) {
                setAnalysis(analysisData);
            }

            // Clear previous chart
            if (chartRef.current) {
                chartRef.current.remove();
                chartRef.current = null;
            }

            const chart = createChart(chartContainerRef.current, {
                layout: {
                    background: { type: ColorType.Solid, color: "transparent" },
                    textColor: "#9ca3af",
                    fontSize: 12,
                },
                grid: {
                    vertLines: { color: "rgba(255,255,255,0.04)" },
                    horzLines: { color: "rgba(255,255,255,0.04)" },
                },
                crosshair: {
                    mode: CrosshairMode.Normal,
                    vertLine: { color: "rgba(6,182,212,0.3)", labelBackgroundColor: "#06b6d4" },
                    horzLine: { color: "rgba(6,182,212,0.3)", labelBackgroundColor: "#06b6d4" },
                },
                rightPriceScale: {
                    borderColor: "rgba(255,255,255,0.1)",
                },
                timeScale: {
                    borderColor: "rgba(255,255,255,0.1)",
                    timeVisible: false,
                },
                width: chartContainerRef.current.clientWidth,
                height: 450,
            });

            chartRef.current = chart;

            // Candlestick series
            const candleSeries = chart.addSeries(CandlestickSeries, {
                upColor: "#06b6d4",
                downColor: "#ef4444",
                borderUpColor: "#06b6d4",
                borderDownColor: "#ef4444",
                wickUpColor: "#06b6d4",
                wickDownColor: "#ef4444",
            });

            candleSeries.setData(chartData.candles as CandlestickData[]);

            // Volume histogram
            const volumeSeries = chart.addSeries(HistogramSeries, {
                priceFormat: { type: "volume" },
                priceScaleId: "volume",
            });

            chart.priceScale("volume").applyOptions({
                scaleMargins: { top: 0.85, bottom: 0 },
            });

            volumeSeries.setData(chartData.volumes as HistogramData[]);

            // EMA overlays
            if (analysisData?.ema20?.length) {
                const ema20Series = chart.addSeries(LineSeries, {
                    color: "#fbbf24",
                    lineWidth: 1,
                    title: "EMA 20",
                    priceLineVisible: false,
                    lastValueVisible: false,
                });
                ema20Series.setData(analysisData.ema20 as LineData[]);
            }

            if (analysisData?.ema50?.length) {
                const ema50Series = chart.addSeries(LineSeries, {
                    color: "#a78bfa",
                    lineWidth: 1,
                    title: "EMA 50",
                    priceLineVisible: false,
                    lastValueVisible: false,
                });
                ema50Series.setData(analysisData.ema50 as LineData[]);
            }

            // Support/Resistance price lines
            if (analysisData?.support) {
                for (const level of analysisData.support) {
                    candleSeries.createPriceLine({
                        price: level,
                        color: "#22c55e",
                        lineWidth: 1,
                        lineStyle: 2, // dashed
                        axisLabelVisible: true,
                        title: `S ${level}`,
                    });
                }
            }

            if (analysisData?.resistance) {
                for (const level of analysisData.resistance) {
                    candleSeries.createPriceLine({
                        price: level,
                        color: "#ef4444",
                        lineWidth: 1,
                        lineStyle: 2,
                        axisLabelVisible: true,
                        title: `R ${level}`,
                    });
                }
            }

            // Pattern markers
            if (analysisData?.patterns?.length) {
                (candleSeries as any).setMarkers(
                    analysisData.patterns.map((p: any) => ({
                        time: p.time,
                        position: p.position,
                        color: p.color,
                        shape: p.shape,
                        text: p.text,
                    }))
                );
            }

            chart.timeScale().fitContent();

            // Resize handler
            const resizeObserver = new ResizeObserver((entries) => {
                if (entries[0] && chartRef.current) {
                    chartRef.current.applyOptions({
                        width: entries[0].contentRect.width,
                    });
                }
            });
            resizeObserver.observe(chartContainerRef.current);

            setLoading(false);

            return () => {
                resizeObserver.disconnect();
                chart.remove();
            };
        } catch (err: any) {
            setError(err.message);
            setLoading(false);
        }
    }, [symbol]);

    useEffect(() => {
        fetchAndRender();
        return () => {
            if (chartRef.current) {
                chartRef.current.remove();
                chartRef.current = null;
            }
        };
    }, [fetchAndRender]);

    return (
        <div className="rounded-xl border border-glass-border bg-glass overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-3 border-b border-glass-border">
                <div className="flex items-center gap-4">
                    <h3 className="text-lg font-bold text-white">{symbol}</h3>
                    {analysis && (
                        <div className="flex items-center gap-3 text-xs">
                            <span className={`px-2 py-0.5 rounded-full font-medium ${analysis.score >= 75 ? "bg-emerald-500/20 text-emerald-400" :
                                analysis.score >= 50 ? "bg-yellow-500/20 text-yellow-400" :
                                    "bg-gray-500/20 text-gray-400"
                                }`}>
                                Score: {analysis.score}
                            </span>
                            <span className={`px-2 py-0.5 rounded-full font-medium ${analysis.trend?.direction === "uptrend" ? "bg-emerald-500/20 text-emerald-400" :
                                analysis.trend?.direction === "downtrend" ? "bg-red-500/20 text-red-400" :
                                    "bg-gray-500/20 text-gray-400"
                                }`}>
                                {analysis.trend?.direction || "neutral"}
                            </span>
                            {analysis.setup_type !== "SKIP" && (
                                <span className="px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-400 font-medium">
                                    {analysis.setup_type}
                                </span>
                            )}
                        </div>
                    )}
                </div>
                <div className="flex items-center gap-3">
                    {/* Legend */}
                    <div className="flex items-center gap-3 text-[10px] text-gray-500">
                        <span className="flex items-center gap-1">
                            <span className="w-3 h-[2px] bg-yellow-400 inline-block"></span> EMA20
                        </span>
                        <span className="flex items-center gap-1">
                            <span className="w-3 h-[2px] bg-violet-400 inline-block"></span> EMA50
                        </span>
                        <span className="flex items-center gap-1">
                            <span className="w-3 h-[2px] bg-emerald-500 inline-block" style={{ borderTop: "1px dashed" }}></span> Support
                        </span>
                        <span className="flex items-center gap-1">
                            <span className="w-3 h-[2px] bg-red-500 inline-block" style={{ borderTop: "1px dashed" }}></span> Resistance
                        </span>
                    </div>
                    {onClose && (
                        <button
                            onClick={onClose}
                            className="text-gray-500 hover:text-white transition-colors text-lg leading-none"
                        >
                            &times;
                        </button>
                    )}
                </div>
            </div>

            {/* Chart */}
            <div className="relative">
                {loading && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/50 z-10">
                        <div className="text-gray-400 text-sm">Loading chart...</div>
                    </div>
                )}
                {error && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/50 z-10">
                        <div className="text-red-400 text-sm">{error}</div>
                    </div>
                )}
                <div ref={chartContainerRef} />
            </div>

            {/* FVG Zones info */}
            {analysis?.fvgs && analysis.fvgs.length > 0 && (
                <div className="px-5 py-2 border-t border-glass-border flex items-center gap-3 text-xs">
                    <span className="text-gray-500 font-medium">FVG Zones:</span>
                    {analysis.fvgs.map((fvg, i) => (
                        <span
                            key={i}
                            className={`px-2 py-0.5 rounded ${fvg.type === "bullish" ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"
                                }`}
                        >
                            {fvg.type === "bullish" ? "Bull" : "Bear"} FVG: {fvg.low} - {fvg.high}
                        </span>
                    ))}
                </div>
            )}
        </div>
    );
}
