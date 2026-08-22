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
import {
  generateUsers,
  generateStats,
  generateHistory,
  generateCategoryData,
  PERFORMANCE,
} from "../data/mockData";
import { networkApi } from "../services/api";
import "../styles/pages.css";

export default function Dashboard() {
  const [users, setUsers] = useState([]);
  const [history, setHistory] = useState(() => generateHistory());
  const [perf, setPerf] = useState(() => PERFORMANCE());
  const [allocating, setAllocating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [live, setLive] = useState(false);

  // Skeleton loader on first mount
  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 900);
    return () => clearTimeout(t);
  }, []);

  // LIVE: pull real registered users + live usage from the backend
  // every 3s. All devices see identical server-side values.
  useEffect(() => {
    let stop = false;
    const pull = async () => {
      try {
        const res = await networkApi.users();
        if (!stop && res?.ok && Array.isArray(res.users) && res.users.length > 0) {
          setUsers(res.users);
          setLive(true);
        }
      } catch {
        /* keep last known data */
      }
    };
    pull();
    const id = setInterval(pull, 3000);
    return () => {
      stop = true;
      clearInterval(id);
    };
  }, []);

  // Fallback: if backend has no accounts yet, show simulated users
  // so the dashboard is never empty.
  useEffect(() => {
    if (!loading && !live && users.length === 0) {
      setUsers(generateUsers());
    }
  }, [loading, live, users.length]);

  // Performance metrics refresh every 5s
  useEffect(() => {
    const id = setInterval(() => setPerf(PERFORMANCE()), 5000);
    return () => clearInterval(id);
  }, []);

  // Push new point into bandwidth history every 5s
  useEffect(() => {
    const id = setInterval(() => {
      setUsers((current) => {
        setHistory((h) => {
          const stats = generateStats(current);
          return {
            labels: [...h.labels.slice(1), "now"],
            values: [...h.values.slice(1), stats.bandwidth],
          };
        });
        return current;
      });
    }, 5000);
    return () => clearInterval(id);
  }, []);

  const stats = useMemo(() => generateStats(users), [users]);

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

      <StatCards stats={stats} />

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
          <h3 className="section-title"><span className="dot" /> Device Category</h3>
          <div className="chart-body">
            <CategoryDoughnut users={users} />
          </div>
        </div>
      </div>

      {/* Table + gauge column */}
      <div className="grid-table-side">
        <UserTable users={users} />

        <div className="side-col">
          <HealthGauge health={stats.health} label={stats.healthLabel} />
          <AIRecommendations />
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
            <div><strong>{stats.connectedUsers}</strong><span>Online users</span></div>
            <div><strong>{stats.bandwidth}</strong><span>Mbps in use</span></div>
            <div><strong>0.{stats.health - 10 > 0 ? stats.health : 90}</strong><span>Fairness index</span></div>
          </div>
        </div>
      </div>

      <AllocationAnimation open={allocating} onComplete={() => setAllocating(false)} />
    </motion.div>
  );
}
