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
import { fetchActiveUsers, getSessionId } from "../services/authService";
import { networkApi, allocationApi } from "../services/api";
import DataSourceLabel from "../components/DataSourceLabel";
import { SIMULATION, REAL_RUNTIME_MEASUREMENT, CALCULATED_FROM_REAL_DATA, UNAVAILABLE } from "../data/provenance";
import "../styles/pages.css";

export default function Dashboard() {
  const { users } = useLiveUsers();
  const { stats, history, live } = useNetworkStats();
  const [allocating, setAllocating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeUsers, setActiveUsers] = useState([]);
  const [activeUsersError, setActiveUsersError] = useState("");
  const [allocationResult, setAllocationResult] = useState(null);
  const [allocationError, setAllocationError] = useState("");

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

  const activeUsernames = useMemo(
    () => new Set(activeUsers.map((u) => u.username)),
    [activeUsers]
  );

  const statsComputed = useMemo(
    () => ({
      connectedUsers: activeUsers.length,
      totalUsers: users.length,
      activeDevices: new Set(
        users.filter((u) => activeUsernames.has(u.username)).map((u) => u.device)
      ).size,
      bandwidth: stats.throughput,
      bandwidthSource:
        stats.liveMode ? CALCULATED_FROM_REAL_DATA : SIMULATION,
      bandwidthUnavailable: stats.throughput === null,
      health: stats.health,
      healthLabel: stats.healthLabel,
    }),
    [activeUsernames, users, stats.health, stats.healthLabel, stats.throughput, stats.liveMode, activeUsers.length]
  );

  const perf = useMemo(
    () => ({
      latency: stats.latency,
      packetLoss: stats.packetLoss,
      throughput: stats.throughput,
      jitter: stats.jitter,
      source: stats.source,
      _meta: stats._meta,
    }),
    [stats.latency, stats.packetLoss, stats.throughput, stats.jitter, stats.source, stats._meta]
  );

  const allocationByUserId = useMemo(() => {
    if (!allocationResult?.users) return {};
    const map = {};
    for (const u of allocationResult.users) {
      map[u.user_id] = u;
    }
    return map;
  }, [allocationResult]);

  const displayUsers = useMemo(() => {
    return users.map((u) => {
      const alloc = allocationByUserId[u.username];
      const isActive = activeUsernames.has(u.username);
      const base = {
        ...u,
        status: isActive ? "online" : "offline",
      };
      if (alloc) {
        return {
          ...base,
          allocated: alloc.allocated_bandwidth,
          _allocated_bandwidth: alloc.allocated_bandwidth,
          _utility: alloc.utility,
        };
      }
      return base;
    });
  }, [users, allocationByUserId, activeUsernames]);

  const handleAllocate = async () => {
    setAllocating(true);
    setAllocationResult(null);
    setAllocationError("");

    // The live allocation is server-authoritative: the backend reads
    // the live_sessions table and translates it into a Game Theory
    // request. The frontend therefore sends no user list of its own.
    const payload = {
      total_bandwidth: 40,
      use_live_users: true,
    };

    try {
      const res = await allocationApi.allocate(payload);

      if (res && res.status === "success" && res.result) {
        setAllocationResult(res.result);
      } else if (res && res.offline) {
        setAllocationError("Backend not reachable. Allocation could not be completed.");
      } else if (res && (res.status === "error" || res.status_code === 401)) {
        setAllocationError(res.message || "Allocation failed.");
      } else {
        setAllocationError(res?.message || "Allocation failed.");
      }
    } catch (err) {
      setAllocationError("Network error. Please try again.");
    }
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
    <motion.div
      className="page"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
    >
      {/* Network mode indicator */}
      <div className="mode-indicator">
        <span className="mode-dot" />
        Network Mode:{" "}
        <strong>
          {stats.liveMode ? "LIVE MEASUREMENT" : "RESEARCH SIMULATION"}
        </strong>
        <DataSourceLabel source={stats.source} />
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
        <div>
          <UserTable users={displayUsers} />
          <p className="text-dim" style={{ fontSize: 12, marginTop: 4 }}>
            Device characteristics are simulated because router/AP telemetry is not available.
          </p>
        </div>

        <div className="side-col">
          <HealthGauge health={statsComputed.health} label={statsComputed.healthLabel} _meta={stats._meta} />
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
          <button
            className="btn-gradient alloc-btn"
            onClick={handleAllocate}
            disabled={allocating}
          >
            <FiRefreshCw /> {allocating ? "Allocating..." : "Allocate Bandwidth"}
          </button>
          {allocationError && (
            <div className="alloc-error">{allocationError}</div>
          )}
          <div className="alloc-meta">
            <div><strong>{allocationResult ? allocationResult.number_of_users : statsComputed.connectedUsers}</strong><span>Online users</span></div>
            <div>
              <strong>
                {allocationResult
                  ? allocationResult.total_allocated_bandwidth.toFixed(1)
                  : (statsComputed.bandwidth === null || statsComputed.bandwidth === undefined
                      ? "N/A"
                      : statsComputed.bandwidth.toFixed(1))}
              </strong>
              <span>Mbps allocated</span>
            </div>
            <div><strong>{allocationResult ? allocationResult.utilization_percentage + "%" : "—"}</strong><span>Utilization</span></div>
            <div>
              <strong>{allocationResult ? allocationResult.jain_fairness_index.toFixed(4) : "—"}</strong>
              <span>{allocationResult ? `Fairness (${allocationResult.fairness_status})` : "Fairness index"}</span>
            </div>
          </div>
          {allocationResult && allocationResult.live_source && (
            <div className="alloc-source text-dim">
              Source: live_sessions ({allocationResult.live_source.unique_user_count} unique users,
              {" "}timeout {allocationResult.live_source.timeout_seconds}s)
            </div>
          )}
        </div>
      </div>

      {/* Server-authoritative active users (real-time presence) */}
      <ActiveUsersList
        users={activeUsers}
        error={activeUsersError}
        loading={activeUsers.length === 0 && !activeUsersError}
      />

      <AllocationAnimation
        open={allocating}
        error={allocationError}
        onComplete={() => {
          setAllocating(false);
        }}
      />
    </motion.div>
  );
}
