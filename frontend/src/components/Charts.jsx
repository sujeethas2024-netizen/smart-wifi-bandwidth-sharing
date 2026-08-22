import { useMemo } from "react";
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
import { Line, Bar, Doughnut, Pie } from "react-chartjs-2";
import { useTheme } from "../theme/ThemeContext";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  Filler
);

function useChartOptions() {
  const { theme } = useTheme();
  return useMemo(() => {
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
          displayColors: true,
        },
      },
      scales: {
        x: { grid: { color: grid }, ticks: { color: ticks, font: { size: 10 } } },
        y: {
          grid: { color: grid },
          ticks: { color: ticks, font: { size: 10 } },
          beginAtZero: true,
        },
      },
    };
  }, [theme]);
}

/* ---------- Bandwidth Usage — live Line chart ---------- */
export function BandwidthLine({ history }) {
  const options = useChartOptions();
  const data = useMemo(
    () => ({
      labels: history.labels,
      datasets: [
        {
          label: "Bandwidth (Mbps)",
          data: history.values,
          borderColor: "#2563eb",
          borderWidth: 2.5,
          tension: 0.45,
          fill: true,
          pointRadius: 0,
          pointHoverRadius: 5,
          backgroundColor: (ctx) => {
            const g = ctx.chart.ctx.createLinearGradient(0, 0, 0, ctx.chart.height);
            g.addColorStop(0, "rgba(37,99,235,0.35)");
            g.addColorStop(1, "rgba(37,99,235,0)");
            return g;
          },
        },
      ],
    }),
    [history]
  );
  return <Line data={data} options={options} />;
}

/* ---------- User Consumption — Bar chart ---------- */
export function ConsumptionBar({ users }) {
  const options = useChartOptions();
  const top = [...users].filter((u) => u.status !== "offline").slice(0, 8);
  const data = useMemo(
    () => ({
      labels: top.map((u) => u.username),
      datasets: [
        {
          label: "Usage (Mbps)",
          data: top.map((u) => u.usage),
          backgroundColor: top.map((_, i) =>
            ["#2563eb", "#7c3aed", "#14b8a6", "#f59e0b", "#ef4444", "#3b82f6", "#8b5cf6", "#06b6d4"][i % 8]
          ),
          borderRadius: 8,
          maxBarThickness: 34,
        },
      ],
    }),
    [top]
  );
  return <Bar data={data} options={options} />;
}

/* ---------- Application Category — Bar ---------- */
export function AppCategoryBar({ data }) {
  const options = useChartOptions();
  return <Bar data={data} options={options} />;
}

/* ---------- Device Category — Doughnut ---------- */
export function CategoryDoughnut({ users }) {
  const options = useChartOptions();
  const counts = {};
  users.forEach((u) => {
    if (u.status !== "offline") counts[u.device] = (counts[u.device] || 0) + 1;
  });
  const labels = Object.keys(counts);
  const palette = ["#2563eb", "#7c3aed", "#14b8a6", "#f59e0b", "#ef4444", "#3b82f6", "#8b5cf6", "#06b6d4"];
  const data = useMemo(
    () => ({
      labels,
      datasets: [
        {
          data: Object.values(counts),
          backgroundColor: labels.map((_, i) => palette[i % palette.length]),
          borderColor: "transparent",
          hoverOffset: 12,
          cutout: "62%",
        },
      ],
    }),
    [labels.join(",")]
  );
  return <Doughnut data={data} options={{ ...options, scales: {} }} />;
}

/* ---------- Bandwidth Allocation — Pie ---------- */
export function AllocationPie({ users }) {
  const options = useChartOptions();
  const sorted = [...users].filter((u) => u.status !== "offline");
  const top = sorted.slice(0, 5);
  const rest = sorted.slice(5).reduce((s, u) => s + u.allocated, 0);
  const data = useMemo(
    () => ({
      labels: [...top.map((u) => u.username), "Others"],
      datasets: [
        {
          data: [...top.map((u) => u.allocated), rest],
          backgroundColor: ["#2563eb", "#7c3aed", "#14b8a6", "#f59e0b", "#ef4444", "#64748b"],
          borderColor: "transparent",
          hoverOffset: 12,
        },
      ],
    }),
    [top.map((t) => t.id).join(",")]
  );
  return <Pie data={data} options={{ ...options, scales: {} }} />;
}