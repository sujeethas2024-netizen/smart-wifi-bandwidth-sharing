import { motion } from "framer-motion";
import { FiCpu, FiCheckCircle, FiAlertTriangle, FiInfo, FiZap } from "react-icons/fi";
import "../styles/components.css";

const TONE = {
  success: { icon: <FiCheckCircle />, color: "#22c55e" },
  warning: { icon: <FiAlertTriangle />, color: "#f59e0b" },
  info: { icon: <FiInfo />, color: "#2563eb" },
  accent: { icon: <FiZap />, color: "#7c3aed" },
};

function buildRecommendations(users) {
  const recs = [];
  const online = users.filter((u) => u.status === "online");
  const idle = users.filter((u) => u.status === "idle");
  const offline = users.filter((u) => u.status === "offline");

  if (online.length > 0) {
    const heavy = [...online].sort((a, b) => (b.usage || 0) - (a.usage || 0))[0];
    if (heavy && (heavy.usage || 0) > 15) {
      recs.push({
        id: 1,
        tone: "info",
        text: `Allocate more bandwidth to ${heavy.name || heavy.username} — heavy usage detected (${heavy.usage} Mbps)`,
        action: true,
      });
    }
  }

  if (idle.length > 0) {
    recs.push({
      id: 2,
      tone: "warning",
      text: `${idle.length} idle device${idle.length > 1 ? "s" : ""} detected — consider throttling to preserve capacity`,
      action: true,
    });
  }

  if (offline.length > 2) {
    recs.push({
      id: 3,
      tone: "warning",
      text: `${offline.length} devices offline for extended period — review active allocations`,
      action: false,
    });
  }

  const weakSignal = online.filter((u) => u.signal === "weak");
  if (weakSignal.length > 0) {
    recs.push({
      id: 4,
      tone: "accent",
      text: `Weak signal on ${weakSignal.map((u) => u.device).join(", ")} — check router placement`,
      action: false,
    });
  }

  if (recs.length === 0) {
    recs.push({
      id: 5,
      tone: "success",
      text: "Network running smoothly — all devices within expected usage bounds",
      action: false,
    });
  }

  return recs.slice(0, 4);
}

export default function AIRecommendations({ users = [] }) {
  const recommendations = buildRecommendations(users);

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
        {recommendations.map((r, i) => {
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