import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { FiRefreshCw } from "react-icons/fi";
import Hero from "../components/Hero";
import StatCards from "../components/StatCards";
import UserTable from "../components/UserTable";
import HealthGauge from "../components/HealthGauge";
import PerformanceCards from "../components/PerformanceCards";
import AIRecommendations from "../components/AIRecommendations";
import AllocationAnimation from "../components/AllocationAnimation";
import ActiveUsersList from "../components/ActiveUsersList";
import { BandwidthLine, ConsumptionBar, CategoryDoughnut } from "../components/Charts";
import { useLiveUsers } from "../hooks/useLiveUsers";
import { useNetworkStats } from "../hooks/useNetworkStats";
import { fetchActiveUsers } from "../services/authService";
import { networkApi } from "../services/api";
import DataSourceLabel from "../components/DataSourceLabel";
import { SIMULATION } from "../data/provenance";
import "../styles/pages.css";

export default function Dashboard() {
  const { users } = useLiveUsers();
  const { stats, history, live } = useNetworkStats();
  const [allocating, setAllocating] = useState(false);
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
        // Network error: retain previous data, report error for this cycle
        setActiveUsersError(res.error || "Server unreachable");
      }
    }

    fetchAndPoll();
    intervalId = setInterval(fetchAndPoll, 10000); // 10-second polling

    return () => {
      mounted = false;
      if (intervalId) clearInterval(intervalId);
    };
  }, []);

  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 700);
    return () => clearTimeout(t);
  }, []);

  const onlineUsers = useMemo(
    () => users.filter((u) => u.status === "online" || u.status === "idle"),
    [users]
  );

  const statsComputed = useMemo(
    () => ({
      connectedUsers: onlineUsers.length,
      totalUsers: users.length,
      activeDevices: new Set(onlineUsers.map((u) => u.device)).size,
      bandwidth: onlineUsers.reduce((s, u) => s + (u.usage || 0), 0),
      health: stats.health,
      healthLabel: stats.healthLabel,
    }),
    [onlineUsers, users, stats.health, stats.healthLabel]
  );

  const perf = useMemo(
    () => ({
      latency: stats.latency,
      packetLoss: stats.packetLoss,
      throughput: stats.throughput,
      jitter: stats.jitter,
      source: stats.source,
    }),
    [stats.latency, stats.packetLoss, stats.throughput, stats.jitter, stats.source]
  );

  const handleAllocate = () => setAllocating(true);

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
    <motion.div
      className="page"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
    >
      {/* Network mode indicator */}
      <div className="mode-indicator">
        <span className="mode-dot" />
        Network Mode: <strong>RESEARCH SIMULATION</strong>
        <DataSourceLabel source={SIMULATION} />
      </div>

      <Hero onStart={handleAllocate} />

      <StatCards stats={statsComputed} />

      {/* Charts row */}
      <div className="grid-2-1">
        <div className="chart-card glass">
          <div className="chart-head">
            <h3 className="section-title"><span className="dot" /> Bandwidth Usage — Live</h3>
            <DataSourceLabel source={stats.source} />
          </div>
          <div className="chart-body tall">
            <BandwidthLine history={history} />
          </div>
        </div>

        <div className="chart-card glass">
          <div className="chart-head">
            <h3 className="section-title"><span className="dot" /> Device Category</h3>
            {live && (
              <DataSourceLabel source={SIMULATION} />
            )}
          </div>
          <div className="chart-body">
            <CategoryDoughnut users={users} />
          </div>
        </div>
      </div>

      {/* Table + gauge column */}
      <div className="grid-table-side">
        <UserTable users={users} />

        <div className="side-col">
          <HealthGauge health={statsComputed.health} label={statsComputed.healthLabel} />
          <AIRecommendations users={users} />
        </div>
      </div>

      {/* Bottom row */}
      <PerformanceCards perf={perf} />

      <div className="grid-2">
        <div className="chart-card glass">
          <h3 className="section-title"><span className="dot" /> User Consumption</h3>
          <div className="chart-body">
            <ConsumptionBar users={users} />
          </div>
        </div>

        <div className="allocate-card glass">
          <h3 className="section-title"><span className="dot" /> Re-run Allocation</h3>
          <p className="text-dim">
            Recompute the Nash equilibrium and redistribute bandwidth fairly
            across all connected devices using the game theory engine.
          </p>
          <button className="btn-gradient alloc-btn" onClick={handleAllocate}>
            <FiRefreshCw /> Allocate Bandwidth
          </button>
          <div className="alloc-meta">
            <div><strong>{statsComputed.connectedUsers}</strong><span>Online users</span></div>
            <div><strong>{statsComputed.bandwidth.toFixed(1)}</strong><span>Mbps in use</span></div>
            <div><strong>0.{statsComputed.health > 10 ? statsComputed.health : 90}</strong><span>Fairness index</span></div>
          </div>
        </div>
      </div>

      {/* Server-authoritative active users (real-time presence) */}
      <ActiveUsersList
        users={activeUsers}
        error={activeUsersError}
        loading={activeUsers.length === 0 && !activeUsersError}
      />

      <AllocationAnimation open={allocating} onComplete={() => setAllocating(false)} />
    </motion.div>
  );
}
