import { motion } from "framer-motion";
import { FiUsers, FiMonitor, FiZap, FiActivity } from "react-icons/fi";
import CountUp from "./CountUp";
import { SIMULATION, UNAVAILABLE } from "../data/provenance";
import "../styles/components.css";

const CARDS = [
  {
    key: "users",
    label: "Connected Users",
    icon: <FiUsers />,
    color: "#2563eb",
    suffix: "",
  },
  {
    key: "devices",
    label: "Active Devices",
    icon: <FiMonitor />,
    color: "#7c3aed",
    suffix: "",
  },
  {
    key: "bandwidth",
    label: "Throughput",
    icon: <FiZap />,
    color: "#14b8a6",
    suffix: " Mbps",
  },
  {
    key: "health",
    label: "Network Health",
    icon: <FiActivity />,
    color: "#22c55e",
    suffix: "%",
  },
];

function isUnavailable(meta, key, override) {
  if (override === true) return true;
  if (override === false) return false;
  return meta && meta[`${key}_source`] === UNAVAILABLE;
}

export default function StatCards({ stats }) {
  const values = {
    users: stats.connectedUsers,
    devices: stats.activeDevices,
    bandwidth: stats.bandwidth,
    health: stats.health,
  };

  return (
    <div className="stat-grid">
      {CARDS.map((c, i) => {
        const unavailable = isUnavailable(
          stats._meta,
          c.key,
          stats.bandwidthUnavailable
        );
        return (
          <motion.div
            key={c.key}
            className="stat-card glass glass-hover"
            initial={{ opacity: 0, y: 26, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ delay: i * 0.1, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            whileHover={{ scale: 1.03 }}
          >
            <div
              className="stat-icon"
              style={{
                background: `${c.color}1f`,
                color: c.color,
                boxShadow: `0 6px 18px ${c.color}33`,
              }}
            >
              {c.icon}
            </div>
            <div className="stat-info">
              <span className="stat-label">{c.label}</span>
              <span className="stat-value" style={{ color: c.color }}>
                {unavailable ? (
                  <span className="stat-na">N/A</span>
                ) : (
                  <CountUp value={values[c.key]} suffix={c.suffix} />
                )}
              </span>
            </div>
            <span
              className="stat-spark"
              style={{ background: `linear-gradient(180deg, ${c.color}55, transparent)` }}
            />
          </motion.div>
        );
      })}
    </div>
  );
}