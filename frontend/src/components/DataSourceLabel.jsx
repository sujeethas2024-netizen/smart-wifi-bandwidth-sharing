import { motion } from "framer-motion";
import { SIMULATION } from "../data/provenance";
import "../styles/components.css";

const SOURCE_STYLES = {
  REAL_DATASET: { label: "REAL DATA", color: "#22c55e", bg: "rgba(34,197,94,0.12)" },
  REAL_RUNTIME_MEASUREMENT: { label: "LIVE MEASUREMENT", color: "#2563eb", bg: "rgba(37,99,235,0.12)" },
  CALCULATED_FROM_REAL_DATA: { label: "CALCULATED", color: "#7c3aed", bg: "rgba(124,58,237,0.12)" },
  REAL_USER_INPUT: { label: "USER INPUT", color: "#14b8a6", bg: "rgba(20,184,166,0.12)" },
  SIMULATION: { label: "SIMULATION", color: "#f59e0b", bg: "rgba(245,158,11,0.12)" },
  RESEARCH_SIMULATION: { label: "RESEARCH SIMULATION", color: "#f97316", bg: "rgba(249,115,22,0.12)" },
  USER_INPUT: { label: "USER INPUT", color: "#14b8a6", bg: "rgba(20,184,166,0.12)" },
  UNAVAILABLE: { label: "N/A", color: "#94a3b8", bg: "rgba(148,163,184,0.15)" },
};

export default function DataSourceLabel({ source = SIMULATION, className = "" }) {
  const style = SOURCE_STYLES[source] || SOURCE_STYLES.SIMULATION;
  return (
    <motion.span
      className={`data-source-badge ${className}`}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      title={`Data source: ${source}`}
      style={{
        color: style.color,
        background: style.bg,
        borderColor: `${style.color}44`,
      }}
    >
      {style.label}
    </motion.span>
  );
}
