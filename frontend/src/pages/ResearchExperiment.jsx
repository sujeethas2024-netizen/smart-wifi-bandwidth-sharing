import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { apiFetch } from "../services/api";
import DataSourceLabel from "../components/DataSourceLabel";
import { SIMULATION, CALCULATED_FROM_REAL_DATA } from "../data/provenance";
import "../styles/pages.css";

const DEFAULT_USER_COUNTS = [5, 10, 20, 30, 50, 100, 200, 373];
const STRATEGIES = [
  "Equal Allocation",
  "Proportional Allocation",
  "Priority Allocation",
  "Max-Min Fairness",
  "Alpha-Fair (α=1.5)",
  "Game Theory",
];

const METRIC_LABELS = {
  total_allocated: "Allocated (Mbps)",
  utilization_percentage: "Utilization (%)",
  jain_fairness_index: "Fairness Index",
  average_utility: "Avg Utility",
  computational_time: "Compute Time (s)",
  convergence_iterations: "Conv. Iterations",
  qos_violations: "QoS Violations",
  latency_ms: "Latency (ms)",
  jitter_ms: "Jitter (ms)",
};

const STRATEGY_COLORS = {
  "Equal Allocation": "#2563eb",
  "Proportional Allocation": "#7c3aed",
  "Priority Allocation": "#14b8a6",
  "Max-Min Fairness": "#f59e0b",
  "Alpha-Fair (α=1.5)": "#ef4444",
  "Game Theory": "#10b981",
};

export default function ResearchExperiment() {
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState([]);
  const [config, setConfig] = useState({
    user_counts: DEFAULT_USER_COUNTS,
    total_bandwidth: 100,
    seed: 42,
    repetitions: 30,
    algorithms: STRATEGIES,
  });
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("table");
  const [selectedMetric, setSelectedMetric] = useState("jain_fairness_index");

  const handleRun = async (endpoint = "/api/experiment/run") => {
    setRunning(true);
    setError("");
    setResults([]);
    try {
      const payload = {
        user_counts: config.user_counts,
        total_bandwidth: config.total_bandwidth,
        seed: config.seed,
        repetitions: config.repetitions,
        algorithms: config.algorithms,
      };
      const res = await apiFetch(endpoint, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      if (res?.ok && Array.isArray(res.results)) {
        setResults(res.results);
      } else if (res?.results && Array.isArray(res.results)) {
        setResults(res.results);
      } else {
        setError(res?.message || "Experiment failed");
      }
    } catch {
      setError("Backend not reachable");
    } finally {
      setRunning(false);
    }
  };

  const handleDownload = () => {
    if (!results.length) return;
    const headers = Object.keys(results[0]).join(",");
    const rows = results.map((r) =>
      Object.values(r)
        .map((v) => (typeof v === "string" && v.includes(",") ? `"${v}"` : v))
        .join(",")
    );
    const csv = [headers, ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `experiment_results_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const grouped = useMemo(() => {
    const map = {};
    results.forEach((r) => {
      const key = r.strategy || r.algorithm || "Unknown";
      if (!map[key]) map[key] = [];
      map[key].push(r);
    });
    return map;
  }, [results]);

  const strategies = Object.keys(grouped);

  const chartData = useMemo(() => {
    const datasets = strategies.map((name) => {
      const rows = (grouped[name] || [])
        .filter((r) => r.number_of_users != null)
        .sort((a, b) => (a.number_of_users || 0) - (b.number_of_users || 0));
      return {
        label: name,
        data: rows.map((r) => ({
          x: r.number_of_users,
          y: r[selectedMetric] ?? r[selectedMetric.replace(/_/g, " ")] ?? 0,
        })),
        borderColor: STRATEGY_COLORS[name] || "#64748b",
        backgroundColor: STRATEGY_COLORS[name] || "#64748b",
        tension: 0.3,
        pointRadius: 4,
      };
    });
    return { datasets };
  }, [strategies, grouped, selectedMetric]);

  return (
    <motion.div
      className="page"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="page-head">
        <div>
          <h2 className="page-title">🔬 Research Experiment</h2>
          <p className="text-dim">
            Reproducible scalability experiments comparing allocation strategies
          </p>
        </div>
        <DataSourceLabel source={CALCULATED_FROM_REAL_DATA} />
      </div>

      {/* Experiment configuration */}
      <div className="chart-card glass">
        <h3 className="section-title"><span className="dot" /> Experiment Configuration</h3>
        <div className="exp-config">
          <label>
            User counts (comma-separated)
            <input
              type="text"
              value={config.user_counts.join(", ")}
              onChange={(e) =>
                setConfig((c) => ({
                  ...c,
                  user_counts: e.target.value
                    .split(",")
                    .map((s) => parseInt(s.trim()))
                    .filter((n) => !isNaN(n)),
                }))
              }
            />
          </label>
          <label>
            Total bandwidth (Mbps)
            <input
              type="number"
              value={config.total_bandwidth}
              onChange={(e) =>
                setConfig((c) => ({ ...c, total_bandwidth: parseFloat(e.target.value) || 0 }))
              }
            />
          </label>
          <label>
            Random seed
            <input
              type="number"
              value={config.seed}
              onChange={(e) =>
                setConfig((c) => ({ ...c, seed: parseInt(e.target.value) || 0 }))
              }
            />
          </label>
          <label>
            Repetitions per config
            <input
              type="number"
              value={config.repetitions}
              onChange={(e) =>
                setConfig((c) => ({ ...c, repetitions: parseInt(e.target.value) || 1 }))
              }
            />
          </label>
          <div className="btn-row">
            <button
              className="btn-gradient"
              onClick={() => handleRun("/api/experiment/run")}
              disabled={running}
            >
              {running ? "Running…" : "Run Experiment"}
            </button>
            <button
              className="btn-gradient"
              onClick={() => handleRun("/api/experiment/run-multi-seed")}
              disabled={running}
            >
              {running ? "Running…" : "Run Multi-Seed"}
            </button>
            <button
              className="btn-outline"
              onClick={handleDownload}
              disabled={!results.length}
            >
              Download CSV
            </button>
          </div>
        </div>
        {error && <p className="login-error">⚠️ {error}</p>}
      </div>

      {/* Results tabs */}
      {results.length > 0 && (
        <>
          <div className="tab-bar">
            <button
              className={activeTab === "table" ? "tab active" : "tab"}
              onClick={() => setActiveTab("table")}
            >
              Results Table
            </button>
            <button
              className={activeTab === "chart" ? "tab active" : "tab"}
              onClick={() => setActiveTab("chart")}
            >
              Charts
            </button>
            <button
              className={activeTab === "stats" ? "tab active" : "tab"}
              onClick={() => setActiveTab("stats")}
            >
              Statistics
            </button>
          </div>

          {activeTab === "table" && (
            <div className="chart-card glass">
              <h3 className="section-title"><span className="dot" /> Raw Results</h3>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Strategy</th>
                      <th>Users</th>
                      <th>Allocated (Mbps)</th>
                      <th>Utilization (%)</th>
                      <th>Fairness</th>
                      <th>Avg Utility</th>
                      <th>Compute (s)</th>
                      <th>Iterations</th>
                      <th>QoS Viol.</th>
                      <th>Latency</th>
                      <th>Jitter</th>
                      <th>Seed</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((r, i) => (
                      <motion.tr
                        key={`${r.strategy || r.algorithm}-${r.number_of_users}-${i}`}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: Math.min(i * 0.01, 0.5) }}
                      >
                        <td>{r.strategy || r.algorithm}</td>
                        <td className="mono">{r.number_of_users}</td>
                        <td className="mono">{(r.total_allocated ?? 0).toFixed(2)}</td>
                        <td className="mono">{(r.utilization_percentage ?? 0).toFixed(2)}%</td>
                        <td className="mono">{(r.jain_fairness_index ?? 0).toFixed(4)}</td>
                        <td className="mono">{(r.average_utility ?? 0).toFixed(4)}</td>
                        <td className="mono">{(r.computational_time ?? 0).toFixed(3)}</td>
                        <td className="mono">{r.convergence_iterations ?? "-"}</td>
                        <td className="mono">{r.qos_violations ?? 0}</td>
                        <td className="mono">{(r.latency_ms ?? 0).toFixed(1)}</td>
                        <td className="mono">{(r.jitter_ms ?? 0).toFixed(1)}</td>
                        <td className="mono">{r.seed ?? config.seed}</td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-dim" style={{ marginTop: 12 }}>
                Source: {CALCULATED_FROM_REAL_DATA} — computed from game theory engine + synthetic demand profiles
              </p>
            </div>
          )}

          {activeTab === "chart" && (
            <div className="chart-card glass">
              <h3 className="section-title"><span className="dot" /> {METRIC_LABELS[selectedMetric] || selectedMetric}</h3>
              <div className="chart-controls">
                <label>
                  Metric:
                  <select
                    value={selectedMetric}
                    onChange={(e) => setSelectedMetric(e.target.value)}
                  >
                    {Object.keys(METRIC_LABELS).map((m) => (
                      <option key={m} value={m}>{METRIC_LABELS[m]}</option>
                    ))}
                  </select>
                </label>
              </div>
              <div className="chart-body">
                <LineChart data={chartData} />
              </div>
            </div>
          )}

          {activeTab === "stats" && (
            <div className="chart-card glass">
              <h3 className="section-title"><span className="dot" /> Aggregated Statistics</h3>
              <StatsTable grouped={grouped} />
            </div>
          )}
        </>
      )}
    </motion.div>
  );
}

function LineChart({ data }) {
  const canvasRef = useState(null)[0];
  const setRef = useState(null)[1];
  useEffect(() => {
    const canvas = setRef.current;
    if (!canvas || !data?.datasets?.length) return;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    const W = rect.width;
    const H = rect.height;
    const pad = { top: 20, right: 20, bottom: 40, left: 50 };
    const plotW = W - pad.left - pad.right;
    const plotH = H - pad.top - pad.bottom;

    ctx.clearRect(0, 0, W, H);

    const allX = data.datasets.flatMap((ds) => ds.data.map((pt) => pt.x));
    const allY = data.datasets.flatMap((ds) => ds.data.map((pt) => pt.y));
    const xMin = Math.min(...allX, 0);
    const xMax = Math.max(...allX, 373);
    const yMin = Math.min(...allY, 0);
    const yMax = Math.max(...allY, 1);

    ctx.strokeStyle = "rgba(148,163,184,0.12)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
      const y = pad.top + (plotH / 5) * i;
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(pad.left + plotW, y);
      ctx.stroke();
    }

    ctx.strokeStyle = "#64748b";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(pad.left, pad.top);
    ctx.lineTo(pad.left, pad.top + plotH);
    ctx.lineTo(pad.left + plotW, pad.top + plotH);
    ctx.stroke();

    ctx.fillStyle = "#94a3b8";
    ctx.font = "10px monospace";
    ctx.textAlign = "center";
    const xTicks = 5;
    for (let i = 0; i <= xTicks; i++) {
      const v = xMin + ((xMax - xMin) / xTicks) * i;
      const x = pad.left + ((v - xMin) / (xMax - xMin || 1)) * plotW;
      ctx.fillText(Math.round(v), x, pad.top + plotH + 16);
    }
    ctx.textAlign = "right";
    const yTicks = 5;
    for (let i = 0; i <= yTicks; i++) {
      const v = yMin + ((yMax - yMin) / yTicks) * i;
      const y = pad.top + plotH - ((v - yMin) / (yMax - yMin || 1)) * plotH;
      ctx.fillText(v.toFixed(2), pad.left - 8, y + 3);
    }

    data.datasets.forEach((ds) => {
      ctx.strokeStyle = ds.borderColor;
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      ds.data.forEach((pt, i) => {
        const x = pad.left + ((pt.x - xMin) / (xMax - xMin || 1)) * plotW;
        const y = pad.top + plotH - ((pt.y - yMin) / (yMax - yMin || 1)) * plotH;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();

      ctx.fillStyle = ds.borderColor;
      ds.data.forEach((pt) => {
        const x = pad.left + ((pt.x - xMin) / (xMax - xMin || 1)) * plotW;
        const y = pad.top + plotH - ((pt.y - yMin) / (yMax - yMin || 1)) * plotH;
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
      });
    });

    ctx.textAlign = "left";
    data.datasets.forEach((ds, i) => {
      const lx = pad.left + 10 + i * 120;
      const ly = pad.top + 10;
      ctx.fillStyle = ds.borderColor;
      ctx.fillRect(lx, ly - 6, 12, 3);
      ctx.fillStyle = "#e2e8f0";
      ctx.font = "11px monospace";
      ctx.fillText(ds.label, lx + 16, ly);
    });
  }, [data, setRef]);

  return <canvas ref={setRef} style={{ width: "100%", height: 300 }} />;
}

function StatsTable({ grouped }) {
  const rows = Object.entries(grouped).map(([strategy, items]) => {
    const users = [...new Set(items.map((r) => r.number_of_users))].sort((a, b) => a - b);
    const byUser = {};
    users.forEach((u) => {
      byUser[u] = items.filter((r) => r.number_of_users === u);
    });

    const agg = {};
    users.forEach((u) => {
      const vals = byUser[u];
      agg[u] = {
        count: vals.length,
        mean: mean(vals.map((v) => v.jain_fairness_index ?? 0)),
        std: stddev(vals.map((v) => v.jain_fairness_index ?? 0)),
        min: Math.min(...vals.map((v) => v.jain_fairness_index ?? 0)),
        max: Math.max(...vals.map((v) => v.jain_fairness_index ?? 0)),
      };
    });

    return { strategy, agg };
  });

  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Strategy</th>
            <th>Users</th>
            <th>N</th>
            <th>Mean</th>
            <th>Std Dev</th>
            <th>Min</th>
            <th>Max</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ strategy, agg }) =>
            Object.entries(agg).map(([users, stats]) => (
              <tr key={`${strategy}-${users}`}>
                <td>{strategy}</td>
                <td className="mono">{users}</td>
                <td className="mono">{stats.count}</td>
                <td className="mono">{stats.mean.toFixed(4)}</td>
                <td className="mono">{stats.std.toFixed(4)}</td>
                <td className="mono">{stats.min.toFixed(4)}</td>
                <td className="mono">{stats.max.toFixed(4)}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

function mean(arr) {
  if (!arr.length) return 0;
  return arr.reduce((a, b) => a + b, 0) / arr.length;
}

function stddev(arr) {
  if (arr.length < 2) return 0;
  const m = mean(arr);
  const variance = arr.reduce((sum, val) => sum + (val - m) ** 2, 0) / (arr.length - 1);
  return Math.sqrt(variance);
}
