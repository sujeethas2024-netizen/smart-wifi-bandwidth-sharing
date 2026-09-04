import { motion } from "framer-motion";
import { FiClock, FiAlertTriangle, FiTrendingUp, FiShuffle } from "react-icons/fi";
import CountUp from "./CountUp";
import { UNAVAILABLE } from "../data/provenance";
import "../styles/components.css";

const CARDS = [
  { key: "latency", label: "Latency", icon: <FiClock />, unit: " ms", color: "#2563eb", decimals: 0 },
  { key: "packetLoss", label: "Packet Loss", icon: <FiAlertTriangle />, unit: "%", color: "#ef4444", decimals: 2 },
  { key: "throughput", label: "Throughput", icon: <FiTrendingUp />, unit: " Mbps", color: "#22c55e", decimals: 0 },
  { key: "jitter", label: "Jitter", icon: <FiShuffle />, unit: " ms", color: "#7c3aed", decimals: 0 },
];

function isUnavailable(meta, key) {
  return meta && meta[`${key}_source`] === UNAVAILABLE;
}

export default function PerformanceCards({ perf }) {
  return (
    <div className="perf-grid">
      {CARDS.map((c, i) => {
        const unavailable = isUnavailable(perf._meta, c.key);
        return (
          <motion.div
            key={c.key}
            className="perf-card glass glass-hover"
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.09, duration: 0.45 }}
          >
            <div className="perf-icon" style={{ background: `${c.color}1a`, color: c.color }}>
              {c.icon}
            </div>
            <span className="perf-label">{c.label}</span>
            <span className="perf-value" style={{ color: c.color }}>
              {unavailable ? (
                <span className="perf-na">N/A</span>
              ) : (
                <CountUp value={perf[c.key]} decimals={c.decimals} suffix={c.unit} />
              )}
            </span>
            {!unavailable && (
              <div className="progress-track mini">
                <motion.div
                  className="progress-fill"
                  initial={{ width: 0 }}
                  animate={{
                    width:
                      c.key === "latency"
                        ? `${Math.min(100, perf.latency * 4)}%`
                        : c.key === "jitter"
                        ? `${Math.min(100, perf.jitter * 12)}%`
                        : `${100 - perf[c.key]}%`,
                  }}
                  transition={{ duration: 1 }}
                  style={{ background: `linear-gradient(90deg, ${c.color}77, ${c.color})` }}
                />
              </div>
            )}
          </motion.div>
        );
      })}
    </div>
  );
}