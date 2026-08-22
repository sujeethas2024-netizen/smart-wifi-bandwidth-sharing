import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import NetworkTopology from "../components/NetworkTopology";
import CoverageMap from "../components/CoverageMap";
import { generateUsers, tickUsers } from "../data/mockData";
import "../styles/pages.css";

function SignalRow({ user }) {
  const on = { excellent: 4, good: 3, fair: 2, weak: 1 }[user.signal] || 1;
  const color =
    user.signal === "excellent" ? "#22c55e"
    : user.signal === "good" ? "#14b8a6"
    : user.signal === "fair" ? "#f59e0b"
    : "#ef4444";
  return (
    <motion.div
      className="signal-row glass glass-hover"
      initial={{ opacity: 0, x: -16 }}
      whileInView={{ opacity: 1, x: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.35 }}
    >
      <span className="sig-device">{user.deviceIcon} <strong>{user.device}</strong></span>
      <span className="mono text-dim">{user.ip}</span>
      <div className="sig-blocks">
        {[...Array(10)].map((_, i) => (
          <i key={i} style={{ background: i < Math.round((on / 4) * 10) ? color : "rgba(148,163,184,.2)" }} />
        ))}
      </div>
      <span className="sig-label" style={{ color }}>
        📶 {user.signal.charAt(0).toUpperCase() + user.signal.slice(1)}
      </span>
    </motion.div>
  );
}

export default function Network() {
  const [users, setUsers] = useState(() => generateUsers());

  useEffect(() => {
    const id = setInterval(() => setUsers((prev) => tickUsers(prev)), 3000);
    return () => clearInterval(id);
  }, []);

  return (
    <motion.div
      className="page"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="page-head">
        <div>
          <h2 className="page-title">🌐 Network Map</h2>
          <p className="text-dim">Topology, coverage and live signal strength across your home</p>
        </div>
      </div>

      <NetworkTopology users={users} />

      <CoverageMap />

      <div className="chart-card glass">
        <h3 className="section-title"><span className="dot" /> Live Signal Strength</h3>
        <div className="signal-list">
          {users.filter((u) => u.status !== "offline").slice(0, 8).map((u) => (
            <SignalRow key={u.id} user={u} />
          ))}
        </div>
      </div>
    </motion.div>
  );
}