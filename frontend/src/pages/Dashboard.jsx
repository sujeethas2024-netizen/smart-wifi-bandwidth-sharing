import { motion } from "framer-motion";
import ModeSwitcher from "../components/ModeSwitcher";
import DataSourceLabel from "../components/DataSourceLabel";
import LiveDashboardContent from "../components/LiveDashboardContent";
import ResearchDashboardContent from "../components/ResearchDashboardContent";
import { useDataMode } from "../hooks/useDataMode";
import "../styles/pages.css";

export default function Dashboard() {
  const { mode } = useDataMode();

  return (
    <motion.div
      className="page"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
    >
      <div className="mode-indicator">
        <ModeSwitcher />
        <span style={{ margin: "0 6px", color: "rgba(148,163,184,0.35)" }}>|</span>
        <span className="mode-dot" style={{ background: mode === "live" ? "#22c55e" : "#f59e0b" }} />
        <strong>{mode === "live" ? "LIVE SYSTEM" : "RESEARCH SIMULATION"}</strong>
        <span style={{ margin: "0 8px", color: "rgba(148,163,184,0.35)" }}>|</span>
        <span className="text-dim" style={{ fontSize: 12 }}>
          Frontend Data View
        </span>
      </div>

      {mode === "live" ? <LiveDashboardContent /> : <ResearchDashboardContent />}
    </motion.div>
  );
}
