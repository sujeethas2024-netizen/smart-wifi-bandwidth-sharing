import { motion } from "framer-motion";
import { FiCpu, FiCheckCircle, FiAlertTriangle, FiInfo, FiZap } from "react-icons/fi";
import { RECOMMENDATIONS } from "../data/mockData";
import "../styles/components.css";

const TONE = {
  success: { icon: <FiCheckCircle />, color: "#22c55e" },
  warning: { icon: <FiAlertTriangle />, color: "#f59e0b" },
  info: { icon: <FiInfo />, color: "#2563eb" },
  accent: { icon: <FiZap />, color: "#7c3aed" },
};

export default function AIRecommendations() {
  return (
    <div className="ai-panel glass">
      <div className="ai-head">
        <h3 className="section-title" style={{ marginBottom: 0 }}>
          <span className="dot" /> AI Recommendations
        </h3>
        <span className="ai-chip">
          <FiCpu /> Game Theory Engine
        </span>
      </div>

      <ul className="ai-list">
        {RECOMMENDATIONS.map((r, i) => {
          const t = TONE[r.tone] || TONE.info;
          return (
            <motion.li
              key={r.id}
              initial={{ opacity: 0, x: -18 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08, duration: 0.4 }}
              style={{ borderLeftColor: t.color }}
            >
              <span className="ai-icon" style={{ color: t.color }}>{t.icon}</span>
              <p>{r.text}</p>
              {r.action && (
                <button className="ai-apply">Apply</button>
              )}
            </motion.li>
          );
        })}
      </ul>

      <div className="ai-footer">
        <span className="pulse-dot" style={{ background: "#22c55e" }} />
        Model retrained 12 min ago · Confidence 96%
      </div>
    </div>
  );
}