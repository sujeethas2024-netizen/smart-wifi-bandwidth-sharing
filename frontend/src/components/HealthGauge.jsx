import { motion } from "framer-motion";
import CountUp from "./CountUp";
import { UNAVAILABLE } from "../data/provenance";
import "../styles/components.css";

/**
 * Semi-circular SVG gauge showing network health percentage.
 */
export default function HealthGauge({ health = 0, label = "Excellent", _meta }) {
  const R = 80;
  const CX = 110;
  const CY = 100;
  // Arc from 180° to 360° (semi circle)
  const circumference = Math.PI * R;
  const unavailable = _meta && _meta.health_source === UNAVAILABLE;
  const displayHealth = unavailable ? 0 : health;
  const offset = circumference * (1 - displayHealth / 100);

  const color =
    unavailable ? "#94a3b8" : health >= 90 ? "#22c55e" : health >= 75 ? "#14b8a6" : health >= 65 ? "#f59e0b" : "#ef4444";

  return (
    <div className="health-gauge glass glass-hover">
      <h3 className="section-title"><span className="dot" /> Network Health</h3>

      <div className="gauge-wrap">
        <svg viewBox="0 0 220 130" className="gauge-svg">
          {/* Track */}
          <path
            d={`M ${CX - R} ${CY} A ${R} ${R} 0 0 1 ${CX + R} ${CY}`}
            fill="none"
            stroke="rgba(148,163,184,0.18)"
            strokeWidth="16"
            strokeLinecap="round"
          />
          {/* Value arc */}
          <motion.path
            d={`M ${CX - R} ${CY} A ${R} ${R} 0 0 1 ${CX + R} ${CY}`}
            fill="none"
            stroke={color}
            strokeWidth="16"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.4, ease: [0.22, 1, 0.36, 1] }}
            style={{ filter: `drop-shadow(0 0 8px ${color}88)` }}
          />
          {/* Needle dot at arc end */}
        </svg>

        <div className="gauge-center">
          <span className="gauge-value" style={{ color }}>
            {unavailable ? (
              <span className="gauge-na">N/A</span>
            ) : (
              <CountUp value={health} suffix="%" />
            )}
          </span>
          <span className="gauge-label">{unavailable ? "Unavailable" : label}</span>
        </div>
      </div>

      <div className="gauge-scale">
        <span>Poor</span>
        <span>Fair</span>
        <span>Good</span>
        <span style={{ color }}>{unavailable ? "—" : "Excellent"}</span>
      </div>
    </div>
  );
}