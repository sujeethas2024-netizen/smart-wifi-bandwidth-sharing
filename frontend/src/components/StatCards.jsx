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
    label: "Active Profiles",
    icon: <FiMonitor />,
    color: "#7c3aed",
    suffix: "",
  },
  {
    key: "bandwidth",
    label: "Bandwidth Capacity",
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

export const EMPTY_STATS = Object.freeze({
  connectedUsers: null,
  totalUsers: null,
  activeDevices: null,
  bandwidth: null,
  bandwidthSource: UNAVAILABLE,
  bandwidthUnavailable: true,
  bandwidthLabel: "Bandwidth Capacity",
  health: null,
  healthLabel: "N/A",
  _meta: Object.freeze({
    bandwidth_source: UNAVAILABLE,
    latency_source: UNAVAILABLE,
    packetLoss_source: UNAVAILABLE,
    throughput_source: UNAVAILABLE,
    jitter_source: UNAVAILABLE,
    health_source: UNAVAILABLE,
  }),
});

export default function StatCards({ stats = EMPTY_STATS }) {
  const safeStats = stats || EMPTY_STATS;
  const values = {
    users: safeStats.connectedUsers,
    devices: safeStats.activeDevices,
    bandwidth: safeStats.bandwidth,
    health: safeStats.health,
  };
  const labels = {
    bandwidth: safeStats.bandwidthLabel || CARDS[2].label,
  };

  return (
    <div className="stat-grid">
      {CARDS.map((c, i) => {
        const unavailable =
          values[c.key] === null ||
          values[c.key] === undefined ||
          isUnavailable(
            safeStats._meta,
            c.key,
            c.key === "bandwidth" ? safeStats.bandwidthUnavailable : undefined
          );
        const label = labels[c.key] || c.label;
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
              <span className="stat-label">{label}</span>
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