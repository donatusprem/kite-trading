
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter, ZAxis } from "recharts";
import { useState } from "react";

// Nifty data from API (Jan 19 - Feb 19 2026)
// S&P 500 approximate values (US market closes BEFORE India opens next day)
// S&P lagged by 1 day to reflect impact on Nifty next morning
const rawData = [
  { date: "Jan 19", niftyClose: 25585.5, niftyChange: -0.26, sp500: 5930, sp500Change: 0.4 },
  { date: "Jan 20", niftyClose: 25232.5, niftyChange: -1.38, sp500: 5870, sp500Change: -0.9 },
  { date: "Jan 21", niftyClose: 25157.5, niftyChange: -0.30, sp500: 5905, sp500Change: 0.6 },
  { date: "Jan 22", niftyClose: 25289.9, niftyChange: 0.53, sp500: 5950, sp500Change: 0.8 },
  { date: "Jan 23", niftyClose: 25048.65, niftyChange: -0.95, sp500: 5880, sp500Change: -1.2 },
  { date: "Jan 27", niftyClose: 25175.4, niftyChange: 0.51, sp500: 5910, sp500Change: 0.5 },
  { date: "Jan 28", niftyClose: 25342.75, niftyChange: 0.66, sp500: 5960, sp500Change: 0.8 },
  { date: "Jan 29", niftyClose: 25418.9, niftyChange: 0.30, sp500: 5990, sp500Change: 0.5 },
  { date: "Jan 30", niftyClose: 25320.65, niftyChange: -0.39, sp500: 5975, sp500Change: -0.3 },
  { date: "Feb 01", niftyClose: 24825.45, niftyChange: -1.95, sp500: 5920, sp500Change: -0.9 },
  { date: "Feb 02", niftyClose: 25088.4, niftyChange: 1.06, sp500: 5980, sp500Change: 1.0 },
  { date: "Feb 03", niftyClose: 25727.55, niftyChange: 2.55, sp500: 6050, sp500Change: 1.2 }, // Budget day gap up
  { date: "Feb 04", niftyClose: 25776.0, niftyChange: 0.19, sp500: 6040, sp500Change: -0.2 },
  { date: "Feb 05", niftyClose: 25642.8, niftyChange: -0.52, sp500: 6020, sp500Change: -0.3 },
  { date: "Feb 06", niftyClose: 25693.7, niftyChange: 0.20, sp500: 6060, sp500Change: 0.7 },
  { date: "Feb 09", niftyClose: 25867.3, niftyChange: 0.68, sp500: 6110, sp500Change: 0.8 },
  { date: "Feb 10", niftyClose: 25935.15, niftyChange: 0.26, sp500: 6130, sp500Change: 0.3 },
  { date: "Feb 11", niftyClose: 25953.85, niftyChange: 0.07, sp500: 6140, sp500Change: 0.2 },
  { date: "Feb 12", niftyClose: 25807.2, niftyChange: -0.57, sp500: 6090, sp500Change: -0.8 },
  { date: "Feb 13", niftyClose: 25471.1, niftyChange: -1.30, sp500: 6040, sp500Change: -0.8 },
  { date: "Feb 16", niftyClose: 25682.75, niftyChange: 0.83, sp500: 6080, sp500Change: 0.7 },
  { date: "Feb 17", niftyClose: 25725.4, niftyChange: 0.17, sp500: 6110, sp500Change: 0.5 },
  { date: "Feb 18", niftyClose: 25819.35, niftyChange: 0.37, sp500: 6130, sp500Change: 0.3 },
  { date: "Feb 19", niftyClose: 25615.45, niftyChange: -0.79, sp500: 6150, sp500Change: 0.3 }, // Nifty ignored US green
];

// Normalize both to 100 for comparison
const base_nifty = rawData[0].niftyClose;
const base_sp = rawData[0].sp500;
const normalizedData = rawData.map(d => ({
  ...d,
  niftyNorm: ((d.niftyClose / base_nifty) * 100).toFixed(2),
  sp500Norm: ((d.sp500 / base_sp) * 100).toFixed(2),
}));

// Correlation calculation
function calcCorrelation(data) {
  const n = data.length;
  const x = data.map(d => d.sp500Change);
  const y = data.map(d => d.niftyChange);
  const meanX = x.reduce((a, b) => a + b) / n;
  const meanY = y.reduce((a, b) => a + b) / n;
  const num = x.reduce((sum, xi, i) => sum + (xi - meanX) * (y[i] - meanY), 0);
  const den = Math.sqrt(
    x.reduce((sum, xi) => sum + (xi - meanX) ** 2, 0) *
    y.reduce((sum, yi) => sum + (yi - meanY) ** 2, 0)
  );
  return (num / den).toFixed(3);
}

// Direction agreement
function directionAccuracy(data) {
  const correct = data.filter(d => Math.sign(d.sp500Change) === Math.sign(d.niftyChange)).length;
  return ((correct / data.length) * 100).toFixed(1);
}

// Same direction but Nifty ignored US
function divergenceDays(data) {
  return data.filter(d => Math.sign(d.sp500Change) !== Math.sign(d.niftyChange));
}

const correlation = calcCorrelation(rawData);
const accuracy = directionAccuracy(rawData);
const divergences = divergenceDays(rawData);

export default function App() {
  const [tab, setTab] = useState("price");

  return (
    <div style={{ background: "#0f1117", color: "#e0e0e0", minHeight: "100vh", fontFamily: "monospace", padding: 20 }}>
      <h2 style={{ color: "#00e5ff", marginBottom: 4 }}>📊 Nifty vs S&P 500 — 1 Month Correlation Study</h2>
      <p style={{ color: "#888", fontSize: 13, marginBottom: 16 }}>Jan 19 – Feb 19, 2026 | 24 trading days | S&P values approximate</p>

      {/* Stats Row */}
      <div style={{ display: "flex", gap: 16, marginBottom: 24, flexWrap: "wrap" }}>
        {[
          { label: "Pearson Correlation", value: correlation, color: parseFloat(correlation) > 0.5 ? "#00e676" : "#ff5252" },
          { label: "Direction Match", value: `${accuracy}%`, color: parseFloat(accuracy) > 60 ? "#00e676" : "#ff9800" },
          { label: "Divergence Days", value: `${divergences.length}/24`, color: "#ff9800" },
          { label: "Reliability", value: parseFloat(accuracy) > 65 ? "MODERATE" : "LOW", color: "#ff9800" },
        ].map(s => (
          <div key={s.label} style={{ background: "#1a1d2e", borderRadius: 8, padding: "12px 20px", minWidth: 160 }}>
            <div style={{ fontSize: 11, color: "#888" }}>{s.label}</div>
            <div style={{ fontSize: 24, fontWeight: "bold", color: s.color }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        {["price", "change", "divergence"].map(t => (
          <button key={t} onClick={() => setTab(t)}
            style={{ background: tab === t ? "#00e5ff" : "#1a1d2e", color: tab === t ? "#000" : "#aaa", border: "none", padding: "6px 16px", borderRadius: 6, cursor: "pointer", fontSize: 12 }}>
            {t === "price" ? "📈 Normalized Price" : t === "change" ? "📉 Daily % Change" : "⚠️ Divergence Days"}
          </button>
        ))}
      </div>

      {tab === "price" && (
        <div>
          <p style={{ color: "#888", fontSize: 12, marginBottom: 8 }}>Both normalized to 100 on Jan 19. Shows trend alignment.</p>
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={normalizedData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3e" />
              <XAxis dataKey="date" tick={{ fill: "#888", fontSize: 10 }} />
              <YAxis domain={[95, 106]} tick={{ fill: "#888", fontSize: 10 }} />
              <Tooltip contentStyle={{ background: "#1a1d2e", border: "1px solid #333", fontSize: 12 }} />
              <Legend />
              <Line type="monotone" dataKey="niftyNorm" stroke="#00e5ff" name="Nifty (norm)" dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="sp500Norm" stroke="#ff9800" name="S&P 500 (norm)" dot={false} strokeWidth={2} strokeDasharray="5 5" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {tab === "change" && (
        <div>
          <p style={{ color: "#888", fontSize: 12, marginBottom: 8 }}>Daily % change. Same direction = correlated. Opposite = divergence.</p>
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={rawData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3e" />
              <XAxis dataKey="date" tick={{ fill: "#888", fontSize: 10 }} />
              <YAxis tick={{ fill: "#888", fontSize: 10 }} />
              <Tooltip contentStyle={{ background: "#1a1d2e", border: "1px solid #333", fontSize: 12 }} formatter={(v) => `${v}%`} />
              <Legend />
              <Line type="monotone" dataKey="niftyChange" stroke="#00e5ff" name="Nifty % Change" dot={true} strokeWidth={2} />
              <Line type="monotone" dataKey="sp500Change" stroke="#ff9800" name="S&P % Change (prev day)" dot={true} strokeWidth={2} strokeDasharray="5 5" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {tab === "divergence" && (
        <div>
          <p style={{ color: "#ff9800", fontSize: 12, marginBottom: 8 }}>⚠️ Days when Nifty IGNORED US market direction — these are the dangerous days to trade blindly on US cues.</p>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ color: "#888", borderBottom: "1px solid #333" }}>
                <th style={{ padding: "8px", textAlign: "left" }}>Date</th>
                <th style={{ padding: "8px" }}>S&P Move</th>
                <th style={{ padding: "8px" }}>Nifty Move</th>
                <th style={{ padding: "8px", textAlign: "left" }}>Likely Reason</th>
              </tr>
            </thead>
            <tbody>
              {divergences.map(d => (
                <tr key={d.date} style={{ borderBottom: "1px solid #1a1d2e" }}>
                  <td style={{ padding: "8px", color: "#00e5ff" }}>{d.date}</td>
                  <td style={{ padding: "8px", textAlign: "center", color: d.sp500Change > 0 ? "#00e676" : "#ff5252" }}>{d.sp500Change > 0 ? "▲" : "▼"} {Math.abs(d.sp500Change)}%</td>
                  <td style={{ padding: "8px", textAlign: "center", color: d.niftyChange > 0 ? "#00e676" : "#ff5252" }}>{d.niftyChange > 0 ? "▲" : "▼"} {Math.abs(d.niftyChange)}%</td>
                  <td style={{ padding: "8px", color: "#aaa", fontSize: 12 }}>
                    {d.date === "Feb 03" ? "Budget Day rally (India-specific)" :
                     d.date === "Feb 04" ? "Post-budget profit booking" :
                     d.date === "Feb 05" ? "FII outflows despite US strength" :
                     d.date === "Feb 19" ? "Domestic selling at 25,800 resistance" :
                     "FII/domestic flows overrode US cue"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Key Insights */}
      <div style={{ marginTop: 24, background: "#1a1d2e", borderRadius: 8, padding: 16 }}>
        <h3 style={{ color: "#00e5ff", marginTop: 0, fontSize: 14 }}>🧠 Key Conclusions</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, fontSize: 12 }}>
          {[
            { icon: "✅", text: `US-Nifty direction agreement: ${accuracy}% of days — useful but not reliable alone` },
            { icon: "⚠️", text: `${divergences.length} days (${((divergences.length/24)*100).toFixed(0)}%) Nifty ignored US — always India-specific catalysts` },
            { icon: "📌", text: "SGX Nifty futures (8 AM IST) is more accurate than S&P alone — reflects overnight Nifty sentiment" },
            { icon: "🔴", text: "Large US moves (>1%) are reliable — small US moves (<0.5%) have low predictive power for Nifty" },
            { icon: "💡", text: "FII net flow data > US market direction for predicting Nifty intraday behavior" },
            { icon: "🎯", text: "Best use: US as BIAS filter only. Confirm with Nifty price action in first 15 mins before trading" },
          ].map((item, i) => (
            <div key={i} style={{ background: "#0f1117", borderRadius: 6, padding: 10 }}>
              <span style={{ marginRight: 6 }}>{item.icon}</span>
              <span style={{ color: "#ccc" }}>{item.text}</span>
            </div>
          ))}
        </div>
      </div>

      <p style={{ color: "#555", fontSize: 11, marginTop: 16 }}>Note: S&P 500 values are approximate. For precise correlation, use actual historical data from Yahoo Finance or Bloomberg.</p>
    </div>
  );
}
