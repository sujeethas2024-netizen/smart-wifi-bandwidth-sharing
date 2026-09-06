import { useMemo, useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useLiveUsers } from "../hooks/useLiveUsers";
import { getCurrentUser } from "../services/authService";
import "../styles/pages.css";

export default function MyUsage() {
  const user = getCurrentUser();
  const { users } = useLiveUsers();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 700);
    return () => clearTimeout(t);
  }, []);

  const myDevices = useMemo(() => {
    const seed = (user?.username || "user").length;
    return users.slice(seed % 5, (seed % 5) + 3);
  }, [users, user]);

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
      </div>

      <div className="stat-grid">
        {[
          { label: "Weekly Usage", suffix: " GB", color: "#2563eb" },
          { label: "Monthly Quota", suffix: " GB", color: "#7c3aed" },
          { label: "Quota Remaining", suffix: " GB", color: "#22c55e" },
          { label: "Avg Daily Usage", suffix: " GB", color: "#14b8a6" },
        ].map((c, i) => (
          <motion.div key={c.label} className="stat-card glass glass-hover"
            initial={{ opacity: 0, y: 22 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}>
            <div className="stat-info">
              <span className="stat-label">{c.label}</span>
              <span className="stat-value" style={{ color: c.color }}>
                <span className="stat-na">N/A</span>
              </span>
              <span className="text-dim" style={{ fontSize: 11, display: 'block', marginTop: 4 }}>
                Per-user traffic telemetry unavailable
              </span>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="chart-card glass">
        <div className="chart-head">
          <h3 className="section-title"><span className="dot" /> My Usage — Last 24 Hours</h3>
        </div>
        <div className="chart-body tall" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ textAlign: 'center', color: 'var(--text-dim)' }}>
            <p style={{ fontSize: '2rem', marginBottom: 8 }}>📊</p>
            <p><strong>Per-user traffic telemetry unavailable</strong></p>
            <p style={{ fontSize: '0.8rem' }}>Router/AP telemetry is required for historical usage data.</p>
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="chart-card glass">
          <div className="chart-head">
            <h3 className="section-title"><span className="dot" /> My Traffic by App</h3>
          </div>
          <div className="chart-body" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ textAlign: 'center', color: 'var(--text-dim)' }}>
              <p style={{ fontSize: '2rem', marginBottom: 8 }}>📱</p>
              <p><strong>Per-app traffic telemetry unavailable</strong></p>
              <p style={{ fontSize: '0.8rem' }}>Requires router/AP telemetry.</p>
            </div>
          </div>
        </div>

        <div className="chart-card glass">
          <div className="chart-head">
            <h3 className="section-title"><span className="dot" /> Weekly Consumption</h3>
          </div>
          <div className="chart-body" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ textAlign: 'center', color: 'var(--text-dim)' }}>
              <p style={{ fontSize: '2rem', marginBottom: 8 }}>📅</p>
              <p><strong>Weekly consumption telemetry unavailable</strong></p>
              <p style={{ fontSize: '0.8rem' }}>Requires router/AP telemetry.</p>
            </div>
          </div>
        </div>
      </div>

      <div className="chart-card glass">
        <h3 className="section-title"><span className="dot" /> My Devices</h3>
        <p className="text-dim" style={{ fontSize: 12, marginTop: -8, marginBottom: 8 }}>
          Device characteristics are simulated because router/AP telemetry is not available.
        </p>
        <div className="device-grid">
          {myDevices.map((d, i) => (
            <motion.div
              key={d.id}
              className="device-card glass glass-hover"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              <div className="device-top">
                <span className="device-emoji">{d.deviceIcon}</span>
                <div>
                  <h4>{d.device}</h4>
                  <p className="mono text-dim">{d.ip}</p>
                </div>
                <span className={`badge ${d.status === "online" ? "badge-success" : d.status === "idle" ? "badge-warning" : "badge-danger"}`}>
                  {d.status === "online" ? "🟢 Active" : d.status === "idle" ? "🟡 Idle" : "🔴 Offline"}
                </span>
              </div>
              <div className="device-meta">
                <div className="meta-row"><span className="text-dim">MAC</span><strong className="mono">{d.mac}</strong></div>
                <div className="meta-row"><span className="text-dim">Room</span><strong className="mono">{d.room || "—"}</strong></div>
                <div className="meta-row"><span className="text-dim">Signal</span><strong className="mono">{d.signal || "—"}</strong></div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      <motion.div className="info-banner glass" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
        💡
        <p>
          Per-user traffic consumption requires router/AP telemetry and is unavailable in this deployment.
          Device characteristics are simulated for demonstration purposes.
        </p>
      </motion.div>
    </motion.div>
  );
}