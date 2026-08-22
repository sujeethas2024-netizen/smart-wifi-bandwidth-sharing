import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { BandwidthLine, ConsumptionBar, CategoryDoughnut, AllocationPie, AppCategoryBar } from "../components/Charts";
import {
  generateUsers,
  generateHistory,
  generateCategoryData,
  tickUsers,
} from "../data/mockData";
import "../styles/pages.css";

export default function Analytics() {
  const [users, setUsers] = useState(() => generateUsers());
  const [history, setHistory] = useState(() => generateHistory(30));
  const [categoryData] = useState(() => generateCategoryData());

  useEffect(() => {
    const id = setInterval(() => {
      setUsers((prev) => tickUsers(prev));
      setHistory((h) => ({
        labels: [...h.labels.slice(1), "now"],
        values: [...h.values.slice(1), Math.max(35, Math.min(98, h.values[h.values.length - 1] + Math.round(Math.random() * 14 - 7)))],
      }));
    }, 3000);
    return () => clearInterval(id);
  }, []);

  const totalAllocated = useMemo(
    () => users.reduce((s, u) => s + u.allocated, 0),
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