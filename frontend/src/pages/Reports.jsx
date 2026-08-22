import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { jsPDF } from "jspdf";
import { FiDownload, FiFileText, FiCalendar, FiClock } from "react-icons/fi";
import { generateUsers, generateStats, PERFORMANCE } from "../data/mockData";
import "../styles/pages.css";

const REPORT_TYPES = [
  {
    key: "daily",
    title: "Daily Report",
    icon: <FiClock />,
    desc: "Last 24 hours — usage peaks, top consumers, health summary.",
    color: "#2563eb",
  },
  {
    key: "weekly",
    title: "Weekly Report",
    icon: <FiCalendar />,
    desc: "7-day trends — fairness index evolution, device activity patterns.",
    color: "#14b8a6",
  },
  {
    key: "monthly",
    title: "Monthly Report",
    icon: <FiFileText />,
    desc: "30-day overview — capacity planning and SLA compliance.",
    color: "#7c3aed",
  },
];

export default function Reports() {
  const [generating, setGenerating] = useState(null);
  const users = useMemo(() => generateUsers(), []);
  const stats = useMemo(() => generateStats(users), [users]);
  const perf = useMemo(() => PERFORMANCE(), []);

  const downloadReport = (type) => {
    setGenerating(type.key);
    setTimeout(() => {
      const doc = new jsPDF();
      const now = new Date().toLocaleString();

      // Header
      doc.setFillColor(15, 23, 42);
      doc.rect(0, 0, 210, 34, "F");
      doc.setTextColor(248, 250, 252);
      doc.setFontSize(18);
      doc.text("Smart WiFi Bandwidth Sharing", 14, 16);
      doc.setFontSize(11);
      doc.setTextColor(148, 163, 184);
      doc.text(`${type.title} — Network Performance`, 14, 26);

      // Meta
      doc.setTextColor(30, 41, 59);
      doc.setFontSize(10);
      doc.text(`Generated: ${now}`, 14, 44);
      doc.text(`Report Type: ${type.title}`, 14, 50);

      // KPI section
      doc.setFontSize(13);
      doc.setFont(undefined, "bold");
      doc.text("Key Metrics", 14, 62);
      doc.setFont(undefined, "normal");
      doc.setFontSize(10);
      const kpis = [
        [`Connected Users`, `${stats.connectedUsers}`],
        [`Active Devices`, `${stats.activeDevices}`],
        [`Current Bandwidth`, `${stats.bandwidth} Mbps`],
        [`Network Health`, `${stats.health}% (${stats.healthLabel})`],
        [`Latency`, `${perf.latency} ms`],
        [`Packet Loss`, `${perf.packetLoss}%`],
        [`Throughput`, `${perf.throughput} Mbps`],
        [`Fairness Index`, `0.9${stats.health % 10}`],
      ];
      kpis.forEach(([k, v], i) => {
        const y = 70 + i * 7;
        doc.text(`• ${k}:`, 16, y);
        doc.setFont(undefined, "bold");
        doc.text(String(v), 80, y);
        doc.setFont(undefined, "normal");
      });

      // Top consumers table
      doc.setFontSize(13);
      doc.setFont(undefined, "bold");
      doc.text("Top Bandwidth Consumers", 14, 140);
      doc.setFontSize(10);
      doc.setFont(undefined, "normal");

      const top = [...users]
        .sort((a, b) => b.allocated - a.allocated)
        .slice(0, 8);

      // table header
      doc.setFillColor(37, 99, 235);
      doc.rect(14, 146, 182, 8, "F");
      doc.setTextColor(255, 255, 255);
      doc.text("User", 17, 151.5);
      doc.text("Device", 60, 151.5);
      doc.text("Priority", 100, 151.5);
      doc.text("Usage", 130, 151.5);
      doc.text("Allocated", 160, 151.5);

      doc.setTextColor(30, 41, 59);
      top.forEach((u, i) => {
        const y = 159 + i * 7;
        if (i % 2 === 0) {
          doc.setFillColor(241, 245, 249);
          doc.rect(14, y - 5.5, 182, 7, "F");
        }
        doc.text(u.username, 17, y);
        doc.text(u.device, 60, y);
        doc.text(u.priority, 100, y);
        doc.text(`${u.usage} Mbps`, 130, y);
        doc.text(`${u.allocated} Mbps`, 160, y);
      });

      // Footer
      doc.setFontSize(9);
      doc.setTextColor(148, 163, 184);
      doc.text(
        "Developed by Sujeetha & Rohith — Final Year Project 2026",
        14,
        285
      );

      doc.save(`smart-wifi-${type.key}-report.pdf`);
      setGenerating(null);
    }, 900);
  };

  return (
    <motion.div
      className="page"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="page-head">
        <div>
          <h2 className="page-title">📑 Reports</h2>
          <p className="text-dim">Generate and download network performance reports as PDF</p>
        </div>
      </div>

      <div className="reports-grid">
        {REPORT_TYPES.map((r, i) => (
          <motion.div
            key={r.key}
            className="report-card glass glass-hover"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.12, duration: 0.45 }}
          >
            <span className="report-icon" style={{ background: `${r.color}1c`, color: r.color }}>
              {r.icon}
            </span>
            <h3>{r.title}</h3>
            <p className="text-dim">{r.desc}</p>
            <button
              className="btn-gradient report-btn"
              onClick={() => downloadReport(r)}
              disabled={generating === r.key}
            >
              {generating === r.key ? (
                <>
                  <span className="mini-spinner" /> Generating…
                </>
              ) : (
                <>
                  <FiDownload /> Download PDF
                </>
              )}
            </button>
          </motion.div>
        ))}
      </div>

      {/* Preview summary */}
      <div className="chart-card glass">
        <h3 className="section-title"><span className="dot" /> Report Preview Summary</h3>
        <div className="report-preview">
          <div><strong>{stats.connectedUsers}</strong><span>Connected Users</span></div>
          <div><strong>{stats.bandwidth} Mbps</strong><span>Avg Bandwidth</span></div>
          <div><strong>{stats.health}%</strong><span>Health Score</span></div>
          <div><strong>0.94</strong><span>Fairness Index</span></div>
          <div><strong>{users.length}</strong><span>Total Devices</span></div>
          <div><strong>{perf.latency} ms</strong><span>Avg Latency</span></div>
        </div>
      </div>
    </motion.div>
  );
}