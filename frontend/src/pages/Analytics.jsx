import { useMemo } from "react";
import { motion } from "framer-motion";
import { BandwidthLine, ConsumptionBar, CategoryDoughnut, AllocationPie, AppCategoryBar } from "../components/Charts";
import { useLiveUsers } from "../hooks/useLiveUsers";
import { useNetworkStats } from "../hooks/useNetworkStats";
import "../styles/pages.css";

export default function Analytics() {
  const { users } = useLiveUsers();
  const { history } = useNetworkStats();

  const categoryData = useMemo(() => {
    const counts = {};
    users.forEach((u) => {
      if (u.status !== "offline") {
        counts[u.device] = (counts[u.device] || 0) + 1;
      }
    });
    const labels = Object.keys(counts);
    const palette = ["#2563eb", "#7c3aed", "#14b8a6", "#f59e0b", "#ef4444", "#3b82f6", "#8b5cf6", "#06b6d4"];
    return {
      labels,
      datasets: [
        {
          data: Object.values(counts),
          backgroundColor: labels.map((_, i) => palette[i % palette.length]),
          borderRadius: 8,
        },
      ],
    };
  }, [users]);

  const totalAllocated = useMemo(
    () => users.reduce((s, u) => s + (u.allocated || 0), 0),
    [users]
  );

  return (
    <motion.div
      className="page"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="page-head">
        <div>
          <h2 className="page-title">📈 Analytics</h2>
          <p className="text-dim">Real-time network insights · Total allocated pool: {totalAllocated} Mbps</p>
        </div>
      </div>

      {/* Line — full width */}
      <div className="chart-card glass">
        <div className="chart-head">
          <h3 className="section-title"><span className="dot" /> Bandwidth Usage (Live)</h3>
          <span className="live-chip"><span className="pulse-dot" style={{ background: "#22c55e" }} /> LIVE</span>
        </div>
        <div className="chart-body tall">
          <BandwidthLine history={history} />
        </div>
      </div>

      {/* Bar + Doughnut */}
      <div className="grid-2">
        <div className="chart-card glass">
          <h3 className="section-title"><span className="dot" /> User Consumption</h3>
          <div className="chart-body">
            <ConsumptionBar users={users} />
          </div>
        </div>

        <div className="chart-card glass">
          <h3 className="section-title"><span className="dot" /> Device Category</h3>
          <div className="chart-body">
            <CategoryDoughnut users={users} />
          </div>
        </div>
      </div>

      {/* Pie full width-ish */}
      <div className="chart-card glass">
        <h3 className="section-title"><span className="dot" /> Bandwidth Allocation Share</h3>
        <div className="chart-body pie-wide">
          <AllocationPie users={users} />
        </div>
      </div>

      {/* Category bar */}
      <div className="chart-card glass">
        <h3 className="section-title"><span className="dot" /> Traffic by Application Category</h3>
        <div className="chart-body">
          <AppCategoryBar data={categoryData} />
        </div>
      </div>
    </motion.div>
  );
}