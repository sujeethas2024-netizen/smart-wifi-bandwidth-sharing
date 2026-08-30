import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Doughnut, Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import CountUp from "../components/CountUp";
import { useLiveUsers } from "../hooks/useLiveUsers";
import { useNetworkStats } from "../hooks/useNetworkStats";
import { getCurrentUser } from "../services/authService";
import { SIMULATION } from "../data/provenance";
import "../styles/pages.css";

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, Tooltip, Legend, Filler
);

function useChartTheme() {
  const isDark = document.documentElement.getAttribute("data-theme") !== "light";
  return useMemo(() => ({
    grid: isDark ? "rgba(148,163,184,0.12)" : "rgba(15,23,42,0.08)",
    ticks: isDark ? "#94a3b8" : "#64748b",
    legend: isDark ? "#e2e8f0" : "#334155",
  }), []);
}

export default function MyUsage() {
  const user = getCurrentUser();
  const { users } = useLiveUsers();
  const { stats } = useNetworkStats();
  const [tick, setTick] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 700);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 4000);
    return () => clearInterval(id);
  }, []);

  const theme = useChartTheme();

  const myDevices = useMemo(() => {
    const seed = (user?.username || "user").length;
    return users.slice(seed % 5, (seed % 5) + 3);
  }, [users, user]);

  const myTotal = useMemo(() => myDevices.reduce((s, d) => s + (d.allocated || 0), 0), [myDevices]);
  const myUsed = useMemo(() => myDevices.reduce((s, d) => s + (d.usage || 0), 0), [myDevices]);

  const hourly = useMemo(() => {
    const labels = [];
    const values = [];
    const base = Math.max(2, Math.min(24, myUsed || 10));
    const hour = new Date().getHours();
    for (let i = 23; i >= 0; i--) {
      const h = (hour - i + 24) % 24;
      labels.push(`${String(h).padStart(2, "0")}:00`);
      const active = h >= 8 && h <= 22;
      const v = active ? base + 2 : Math.max(1, base - 3);
      values.push(Math.round(v * 10) / 10);
    }
    return { labels, values };
  }, [tick === 0, myUsed]); // eslint-disable-line

  const categories = useMemo(() => {
    const base = Math.max(5, myUsed || 15);
    const streaming = Math.round(base * 0.35);
    const gaming = Math.round(base * 0.15);
    const browsing = Math.round(base * 0.25);
    const downloads = Math.round(base * 0.15);
    const calls = Math.max(1, base - streaming - gaming - browsing - downloads);
    return {
      labels: ["Streaming", "Gaming", "Browsing", "Downloads", "Calls"],
      datasets: [
        {
          data: [streaming, gaming, browsing, downloads, calls],
          backgroundColor: ["#2563eb", "#7c3aed", "#14b8a6", "#f59e0b", "#ef4444"],
          borderColor: "transparent",
          hoverOffset: 10,
          cutout: "62%",
        },
      ],
    };
  }, [tick, myUsed]);

  const weekly = useMemo(() => {
    const base = Math.max(1, Math.round((myUsed || 5) * 3.5));
    const days = [base - 1, base, base + 1, base, base - 2, base + 2, base + 1].map((v) => Math.max(1, v));
    return {
      labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
      datasets: [
        {
          label: "GB used",
          data: days,
          backgroundColor: "#2563eb",
          borderRadius: 8,
          maxBarThickness: 38,
        },
      ],
    };
  }, [tick, myUsed]);

  const totalGB = weekly.datasets[0].data.reduce((s, v) => s + v, 0);
  const quotaGB = 50;

  const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: theme.legend, usePointStyle: true, boxWidth: 8 } },
      tooltip: {
        backgroundColor: "rgba(15,23,42,0.92)",
        titleColor: "#f8fafc",
        bodyColor: "#cbd5e1",
        padding: 12,
        cornerRadius: 10,
      },
    },
    scales: {
      x: { grid: { color: theme.grid }, ticks: { color: theme.ticks, font: { size: 10 } } },
      y: { grid: { color: theme.grid }, ticks: { color: theme.ticks, font: { size: 10 } }, beginAtZero: true },
    },
  };

  if (loading) {
    return (
      <div className="page">
        <div className="skeleton hero-skel" />
        <div className="stat-grid">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton stat-skel" />
          ))}
        </div>
        <div className="skeleton chart-skel" />
      </div>
    );
  }

  return (
    <motion.div className="page" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
      <div className="page-head">
        <div>
          <h2 className="page-title">📊 My Usage</h2>
          <p className="text-dim">Personal consumption insights for {user?.fullName || user?.username}</p>
        </div>
        <span className="sim-chip">SIMULATION</span>
      </div>

      <div className="stat-grid">
        {[
          { label: "This Week", value: totalGB, suffix: " GB", color: "#2563eb" },
          { label: "Monthly Quota", value: quotaGB, suffix: " GB", color: "#7c3aed" },
          { label: "Quota Left", value: Math.max(0, quotaGB - totalGB), suffix: " GB", color: "#22c55e" },
          { label: "Avg Daily", value: +(totalGB / 7).toFixed(1), suffix: " GB", color: "#14b8a6", decimals: 1 },
        ].map((c, i) => (
          <motion.div key={c.label} className="stat-card glass glass-hover"
            initial={{ opacity: 0, y: 22 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}>
            <div className="stat-info">
              <span className="stat-label">{c.label}</span>
              <span className="stat-value" style={{ color: c.color }}>
                <CountUp value={c.value} decimals={c.decimals || 0} suffix={c.suffix} />
              </span>
            </div>
            <div className="progress-track mini">
              <div className="progress-fill" style={{
                width: c.label === "Monthly Quota" ? "100%" : `${Math.min(100, (c.value / quotaGB) * 100)}%`,
                background: `linear-gradient(90deg, ${c.color}77, ${c.color})`,
              }} />
            </div>
          </motion.div>
        ))}
      </div>

      <div className="chart-card glass">
        <div className="chart-head">
          <h3 className="section-title"><span className="dot" /> My Usage — Last 24 Hours</h3>
          <span className="sim-chip">{SIMULATION}</span>
        </div>
        <div className="chart-body tall">
          <Bar data={{
            labels: hourly.labels,
            datasets: [
              {
                label: "Mbps",
                data: hourly.values,
                backgroundColor: hourly.values.map((v) => (v > 18 ? "#ef4444" : v > 12 ? "#f59e0b" : "#2563eb")),
                borderRadius: 6,
              },
            ],
          }} options={baseOptions} />
        </div>
      </div>

      <div className="grid-2">
        <div className="chart-card glass">
          <div className="chart-head">
            <h3 className="section-title"><span className="dot" /> My Traffic by App</h3>
            <span className="sim-chip">{SIMULATION}</span>
          </div>
          <div className="chart-body">
            <Doughnut data={categories} options={{ ...baseOptions, scales: {} }} />
          </div>
        </div>

        <div className="chart-card glass">
          <div className="chart-head">
            <h3 className="section-title"><span className="dot" /> Weekly Consumption</h3>
            <span className="sim-chip">{SIMULATION}</span>
          </div>
          <div className="chart-body">
            <Bar data={weekly} options={baseOptions} />
          </div>
        </div>
      </div>

      <motion.div className="info-banner glass" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
        💡
        <p>
          Tip: schedule large downloads between 1 AM – 6 AM to keep your peak-hour
          speeds fast and stay within your monthly quota.
        </p>
      </motion.div>
    </motion.div>
  );
}