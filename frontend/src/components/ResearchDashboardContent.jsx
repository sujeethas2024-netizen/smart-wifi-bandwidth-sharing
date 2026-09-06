import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { FiDownload } from "react-icons/fi";
import StatCards from "../components/StatCards";
import UserTable from "../components/UserTable";
import HealthGauge from "../components/HealthGauge";
import AIRecommendations from "../components/AIRecommendations";
import AllocationAnimation from "../components/AllocationAnimation";
import DataSourceLabel from "../components/DataSourceLabel";
import ResearchLineChart from "../components/ResearchLineChart";
import { useResearchData } from "../hooks/useResearchData";
import { RESEARCH_SIMULATION, CALCULATED_FROM_REAL_DATA, SIMULATION } from "../data/provenance";
import "../styles/pages.css";

const METRIC_LABELS = {
  jain_fairness_index: "Fairness Index",
  total_allocated_mean: "Allocated (Mbps)",
  utilization_percentage_mean: "Utilization (%)",
  average_utility_mean: "Avg Utility",
  computational_time_mean: "Compute Time (s)",
  convergence_iterations_mean: "Conv. Iterations",
};

export default function ResearchDashboardContent() {
  const { data, stats, loading, error } = useResearchData();
  const [selectedMetric, setSelectedMetric] = useState("jain_fairness_index");

  const statsComputed = useMemo(() => {
    if (!stats?.latestByStrategy) return null;
    const gameTheory = stats.latestByStrategy["game_theory"] || stats.latestByStrategy["Game Theory"];
    const latestUsers = gameTheory ? gameTheory.number_of_users : null;
    return {
      connectedUsers: latestUsers || stats.userCounts?.[stats.userCounts.length - 1] || "—",
      totalUsers: stats.aggregatedCount || 0,
      activeDevices: Object.keys(stats.latestByStrategy || {}).length,
      bandwidth: gameTheory?.total_allocated_mean || null,
      bandwidthSource: SIMULATION,
      bandwidthUnavailable: true,
      bandwidthLabel: "Research Bandwidth",
      health: null,
      healthLabel: "N/A",
      _meta: { research: true },
    };
  }, [stats]);

  const researchRows = useMemo(() => data?.aggregated || [], [data]);

  const displayUsers = useMemo(() => {
    if (!stats?.latestByStrategy) return [];
    return Object.entries(stats.latestByStrategy).map(([strategy, row]) => ({
      username: strategy.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
      device: "Research",
      status: "online",
      allocated: row.total_allocated_mean,
      usage: row.total_allocated_mean,
      priority: "Research",
      activity: "Research",
      _utility: row.average_utility_mean,
      _fairness: row.jain_fairness_index_mean,
      _convergence: row.convergence_iterations_mean,
    }));
  }, [stats]);

  if (loading) {
    return (
      <div className="page">
        <div className="skeleton hero-skel" />
        <div className="stat-grid">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton stat-skel" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <motion.div
      className="page"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
    >
      <div className="mode-indicator">
        <span className="mode-dot" style={{ background: "#f59e0b" }} />
        <strong>RESEARCH SIMULATION</strong>
        <span style={{ margin: "0 8px", color: "rgba(148,163,184,0.35)" }}>|</span>
        <span className="text-dim" style={{ fontSize: 12 }}>
          Controlled experimental data · {stats?.aggregatedCount || 0} aggregated results
        </span>
        <DataSourceLabel source={RESEARCH_SIMULATION} />
      </div>

      <StatCards stats={statsComputed} />

      <div className="chart-card glass">
        <div className="chart-head">
          <h3 className="section-title"><span className="dot" /> Research Bandwidth Results</h3>
          <DataSourceLabel source={RESEARCH_SIMULATION} />
        </div>
        <div className="chart-body tall">
          <ResearchLineChart
            rows={researchRows}
            metric={selectedMetric}
            label={METRIC_LABELS[selectedMetric] || selectedMetric}
          />
        </div>
        <div className="chart-controls" style={{ marginTop: 12 }}>
          <label>
            Metric:
            <select
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
            >
              {Object.entries(METRIC_LABELS).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div className="grid-table-side">
        <div>
          <div className="chart-card glass">
            <h3 className="section-title"><span className="dot" /> Aggregated Results by Strategy</h3>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Strategy</th>
                    <th>Users</th>
                    <th>N</th>
                    <th>Allocated Mean</th>
                    <th>Utilization Mean</th>
                    <th>Fairness Mean</th>
                    <th>Utility Mean</th>
                    <th>Conv. Iterations</th>
                  </tr>
                </thead>
                <tbody>
                  {researchRows.map((r, i) => (
                    <motion.tr
                      key={`${r.strategy}-${r.number_of_users}-${i}`}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: Math.min(i * 0.005, 0.5) }}
                    >
                      <td>{r.strategy.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}</td>
                      <td className="mono">{r.number_of_users}</td>
                      <td className="mono">{r.n || "—"}</td>
                      <td className="mono">{(r.total_allocated_mean ?? 0).toFixed(2)}</td>
                      <td className="mono">{(r.utilization_percentage_mean ?? 0).toFixed(2)}%</td>
                      <td className="mono">{(r.jain_fairness_index_mean ?? 0).toFixed(4)}</td>
                      <td className="mono">{(r.average_utility_mean ?? 0).toFixed(4)}</td>
                      <td className="mono">{r.convergence_iterations_mean ?? "—"}</td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-dim" style={{ marginTop: 10, fontSize: 11 }}>
              Source: {RESEARCH_SIMULATION} — {stats?.raw_count || 0} raw experiments · {stats?.aggregatedCount || 0} aggregated results
            </p>
          </div>
        </div>

        <div className="side-col">
          <HealthGauge health={null} label="N/A" _meta={{ research: true }} />
          <AIRecommendations users={displayUsers} />
        </div>
      </div>

      {error && <div className="login-error">⚠️ {error}</div>}
    </motion.div>
  );
}
