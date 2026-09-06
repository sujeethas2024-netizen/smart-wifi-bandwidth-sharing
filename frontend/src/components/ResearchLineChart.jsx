import { useMemo } from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { useTheme } from "../theme/ThemeContext";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler
);

const STRATEGY_COLORS = {
  equal: "#2563eb",
  proportional: "#7c3aed",
  priority: "#14b8a6",
  max_min_fairness: "#f59e0b",
  alpha_fair: "#ef4444",
  game_theory: "#10b981",
};

export default function ResearchLineChart({ rows = [], metric = "jain_fairness_index", label }) {
  const { theme } = useTheme();
  const data = useMemo(() => {
    const strategies = [...new Set(rows.map((r) => r.strategy))];
    const datasets = strategies.map((strategy) => {
      const points = rows
        .filter((r) => r.strategy === strategy)
        .sort((a, b) => (a.number_of_users || 0) - (b.number_of_users || 0));
      return {
        label: strategy.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
        data: points.map((r) => ({
          x: r.number_of_users,
          y: r[metric] ?? 0,
        })),
        borderColor: STRATEGY_COLORS[strategy] || "#64748b",
        backgroundColor: STRATEGY_COLORS[strategy] || "#64748b",
        tension: 0.3,
        pointRadius: 4,
      };
    });
    return { datasets };
  }, [rows, metric]);

  const options = useMemo(() => {
    const grid = theme === "dark" ? "rgba(148,163,184,0.12)" : "rgba(15,23,42,0.08)";
    const ticks = theme === "dark" ? "#94a3b8" : "#64748b";
    const legend = theme === "dark" ? "#e2e8f0" : "#334155";
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: legend, usePointStyle: true, boxWidth: 8, font: { size: 11 } },
        },
        tooltip: {
          backgroundColor: "rgba(15,23,42,0.92)",
          titleColor: "#f8fafc",
          bodyColor: "#cbd5e1",
          padding: 12,
          cornerRadius: 10,
        },
      },
      scales: {
        x: {
          type: "linear",
          grid: { color: grid },
          ticks: { color: ticks, font: { size: 10 } },
          title: { display: true, text: "Number of Users", color: ticks },
        },
        y: {
          grid: { color: grid },
          ticks: { color: ticks, font: { size: 10 } },
          beginAtZero: true,
          title: { display: true, text: label, color: ticks },
        },
      },
    };
  }, [theme, label]);

  if (!data.datasets.length) {
    return (
      <div className="chart-empty">
        <span className="chart-empty-icon">📊</span>
        <p>No research data available</p>
      </div>
    );
  }

  return <Line data={data} options={options} />;
}
