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
import { BandwidthLine, ConsumptionBar, CategoryDoughnut } from "../components/Charts";
import { useLiveUsers } from "../hooks/useLiveUsers";
import { useNetworkStats } from "../hooks/useNetworkStats";
import { networkApi } from "../services/api";
import "../styles/pages.css";

export default function Dashboard() {
  const { users } = useLiveUsers();
  const { stats, history, live } = useNetworkStats();
  const [allocating, setAllocating] = useState(false);
  const [loading, setLoading] = useState(true);

  // Skeleton loader on first mount
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
    }),
    [stats.latency, stats.packetLoss, stats.throughput, stats.jitter]
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
      <Hero onStart={handleAllocate} />

      <StatCards stats={statsComputed} />

      {/* Charts row */}
      <div className="grid-2-1">
        <div className="chart-card glass">
          <div className="chart-head">
            <h3 className="section-title"><span className="dot" /> Bandwidth Usage — Live</h3>
            <span className="live-chip"><span className="pulse-dot" style={{ background: "#22c55e" }} /> LIVE</span>
          </div>
          <div className="chart-body tall">
            <BandwidthLine history={history} />
          </div>
        </div>

        <div className="chart-card glass">
          <div className="chart-head">
            <h3 className="section-title"><span className="dot" /> Device Category</h3>
            {live && (
              <span className="live-chip">
                <span className="pulse-dot" style={{ background: "#22c55e" }} /> LIVE
              </span>
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

      <AllocationAnimation open={allocating} onComplete={() => setAllocating(false)} />
    </motion.div>
  );
}
