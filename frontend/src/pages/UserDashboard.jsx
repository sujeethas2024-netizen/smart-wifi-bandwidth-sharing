import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { FiInfo, FiZap, FiWifi, FiActivity, FiShield } from "react-icons/fi";
import CountUp from "../components/CountUp";
import { BandwidthLine } from "../components/Charts";
import { useLiveUsers } from "../hooks/useLiveUsers";
import { useNetworkStats } from "../hooks/useNetworkStats";
import { getCurrentUser, fetchActiveUsers } from "../services/authService";
import "../styles/pages.css";

/* Personal quota ring */
function QuotaRing({ used, total }) {
  const pct = Math.min(100, Math.round((used / total) * 100));
  const R = 78;
  const C = 2 * Math.PI * R;
  const color = pct >= 90 ? "#ef4444" : pct >= 70 ? "#f59e0b" : "#22c55e";
  return (
    <div className="quota-ring-wrap">
      <svg viewBox="0 0 200 200" className="quota-ring">
        <circle cx="100" cy="100" r={R} fill="none" stroke="rgba(148,163,184,.16)" strokeWidth="16" />
        <motion.circle
          cx="100" cy="100" r={R} fill="none"
          stroke={color} strokeWidth="16" strokeLinecap="round"
          strokeDasharray={C}
          initial={{ strokeDashoffset: C }}
          animate={{ strokeDashoffset: C * (1 - pct / 100) }}
          transition={{ duration: 1.4, ease: [0.22, 1, 0.36, 1] }}
          style={{ filter: `drop-shadow(0 0 10px ${color}77)` }}
          transform="rotate(-90 100 100)"
        />
      </svg>
      <div className="quota-center">
        <span className="quota-pct" style={{ color }}><CountUp value={pct} suffix="%" /></span>
        <span className="quota-label">of quota used</span>
      </div>
    </div>
  );
}

export default function UserDashboard() {
  const user = getCurrentUser();
  const { users } = useLiveUsers();
  const { stats, history } = useNetworkStats();
  const [loading, setLoading] = useState(true);
  const [activeUsers, setActiveUsers] = useState([]);
  const [activeUsersError, setActiveUsersError] = useState("");

  useEffect(() => {
    let mounted = true;
    let intervalId = null;

    async function fetchAndPoll() {
      const res = await fetchActiveUsers();
      if (!mounted) return;

      if (res.unauthorized) {
        clearInterval(intervalId);
        setActiveUsers([]);
        setActiveUsersError("Session expired. Please log in again.");
        return;
      }

      if (res.ok) {
        setActiveUsers(res.users || []);
        setActiveUsersError("");
      } else if (res.offline) {
        setActiveUsersError(res.error || "Live user data unavailable");
      }
    }

    fetchAndPoll();
    intervalId = setInterval(fetchAndPoll, 10000);

    return () => {
      mounted = false;
      if (intervalId) clearInterval(intervalId);
    };
  }, []);

  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 700);
    return () => clearTimeout(t);
  }, []);

  const activeUsernames = useMemo(
    () => new Set(activeUsers.map((u) => u.username)),
    [activeUsers]
  );

  // My personal slice of the network (deterministic per username)
  const myDevices = useMemo(() => {
    const seed = (user?.username || "user").length;
    return users.slice(seed % 5, (seed % 5) + 3).map((u) => ({
      ...u,
      status: activeUsernames.has(u.username) ? "online" : "offline",
    }));
  }, [users, user, activeUsernames]);

  const myTotal = useMemo(() => myDevices.reduce((s, d) => s + (d.allocated || 0), 0), [myDevices]);
  const myUsed = useMemo(() => myDevices.reduce((s, d) => s + (d.usage || 0), 0), [myDevices]);

  const netStats = useMemo(() => ({
    connectedUsers: activeUsers.length,
    totalUsers: users.length,
    bandwidth: stats.throughput,
    health: stats.health,
    healthLabel: stats.healthLabel,
    latency: stats.latency,
    packetLoss: stats.packetLoss,
  }), [activeUsers, users, stats.health, stats.healthLabel, stats.throughput, stats.latency, stats.packetLoss]);

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

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
    <motion.div className="page" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}>
      {/* Welcome banner */}
      <motion.div
        className="welcome-banner glass"
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55 }}
      >
        <div className="welcome-text">
          <span className="welcome-tag">👤 User Portal</span>
          <h1>{greeting}, <span className="grad-text">{user?.fullName || user?.username}</span> 👋</h1>
          <p className="text-dim">
            Here's your personal bandwidth overview. This portal is read-only —
            allocations are managed by your network administrator.
          </p>
        </div>
        <div className="welcome-badge">
          <FiShield />
          <div>
            <strong>Read-only access</strong>
            <small>Role: Network User</small>
          </div>
        </div>
      </motion.div>

      {/* Personal KPIs */}
      <div className="stat-grid">
        {[
          { label: "My Allocation", value: myTotal, suffix: " Mbps", color: "#2563eb", icon: <FiZap />, simulated: true },
          { label: "Used Now", value: myUsed, suffix: " Mbps", color: "#14b8a6", icon: <FiActivity />, simulated: true },
          { label: "Remaining", value: Math.max(0, myTotal - myUsed), suffix: " Mbps", color: "#7c3aed", icon: <FiWifi />, simulated: true },
          { label: "Network Health", value: netStats.health, suffix: "%", color: "#22c55e", icon: <FiShield />, simulated: false },
        ].map((c, i) => (
          <motion.div
            key={c.label}
            className="stat-card glass glass-hover"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.09 }}
          >
            <div className="stat-icon" style={{ background: `${c.color}1f`, color: c.color }}>{c.icon}</div>
            <div className="stat-info">
              <span className="stat-label">{c.label}</span>
              <span className="stat-value" style={{ color: c.color }}>
                {c.simulated && (c.value === undefined || c.value === null || c.value === 0) ? (
                  <span className="stat-na">N/A</span>
                ) : (
                  <CountUp value={c.value} suffix={c.suffix} />
                )}
              </span>
              {c.simulated && (
                <span className="text-dim" style={{ fontSize: 10, display: 'block', marginTop: 2 }}>
                  Simulated profile
                </span>
              )}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Quota + live usage */}
      <div className="grid-2-1">
        <div className="chart-card glass">
          <div className="chart-head">
            <h3 className="section-title"><span className="dot" /> My Live Usage</h3>
            <span className="live-chip"><span className="pulse-dot" style={{ background: "#22c55e" }} /> LIVE</span>
          </div>
          <div className="chart-body tall">
            <BandwidthLine history={history} />
          </div>
        </div>

        <div className="quota-card glass">
          <h3 className="section-title"><span className="dot" /> My Quota</h3>
          <QuotaRing used={myUsed} total={myTotal} />
          <div className="quota-meta">
            <div><strong className="mono">{myUsed} Mbps</strong><span>Used</span></div>
            <div><strong className="mono">{Math.max(0, myTotal - myUsed)} Mbps</strong><span>Left</span></div>
            <div><strong className="mono">{myTotal} Mbps</strong><span>Total</span></div>
          </div>
        </div>
      </div>

      {/* My devices */}
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
                <div className="meta-row"><span className="text-dim">Allocated</span><strong className="mono">{d.allocated} Mbps</strong></div>
                <div className="meta-row"><span className="text-dim">Using</span><strong className="mono">{d.usage} Mbps</strong></div>
              </div>
              <div className="progress-track">
                <div className="progress-fill" style={{ width: `${Math.round((d.usage / d.allocated) * 100)}%` }} />
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Read-only network status */}
      <div className="chart-card glass">
        <h3 className="section-title"><span className="dot" /> Network Status (read-only)</h3>
        <div className="netstatus-row">
          <div><strong>{netStats.connectedUsers}</strong><span>Users online</span></div>
          <div>
            <strong>
              {netStats.bandwidth === null || netStats.bandwidth === undefined
                ? "N/A"
                : `${netStats.bandwidth.toFixed(1)} Mbps`}
            </strong>
            <span>Host throughput</span>
          </div>
          <div>
            <strong>
              {netStats.latency === null || netStats.latency === undefined
                ? "N/A"
                : `${netStats.latency} ms`}
            </strong>
            <span>Latency</span>
          </div>
          <div>
            <strong>
              {netStats.packetLoss === null || netStats.packetLoss === undefined
                ? "N/A"
                : `${netStats.packetLoss}%`}
            </strong>
            <span>Packet loss</span>
          </div>
          <div>
            <strong style={{ color: "#22c55e" }}>
              {netStats.health === null || netStats.health === undefined
                ? "N/A"
                : netStats.healthLabel}
            </strong>
            <span>Health</span>
          </div>
        </div>
        {activeUsersError && (
          <p className="text-dim" style={{ marginTop: 8 }}>{activeUsersError}</p>
        )}
      </div>

      {/* Info banner */}
      <motion.div className="info-banner glass" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}>
        <FiInfo />
        <p>
          Need more bandwidth or have an issue? Contact your administrator —
          allocation changes are applied through the game theory engine on the admin console.
        </p>
        <Link to="/network" className="btn-ghost info-link">View Network Status →</Link>
      </motion.div>
    </motion.div>
  );
}