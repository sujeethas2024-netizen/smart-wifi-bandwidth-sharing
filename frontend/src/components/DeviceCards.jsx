import { motion } from "framer-motion";
import "../styles/components.css";

function SignalBars({ level }) {
  const on = { excellent: 4, good: 3, fair: 2, weak: 1 }[level] || 1;
  return (
    <span className={`signal-bars ${level}`}>
      {[0, 1, 2, 3].map((i) => (
        <span key={i} className={i < on ? "on" : ""} />
      ))}
    </span>
  );
}

const STATUS_MAP = {
  online: { cls: "badge-success", label: "🟢 Active" },
  idle: { cls: "badge-warning", label: "🟡 Idle" },
  offline: { cls: "badge-danger", label: "🔴 Offline" },
};

export default function DeviceCards({ users }) {
  return (
    <div className="device-grid">
      {users.map((u, i) => {
        const st = STATUS_MAP[u.status];
        return (
          <motion.div
            key={u.id}
            className="device-card glass glass-hover"
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ delay: (i % 8) * 0.06, duration: 0.45 }}
          >
            <div className="device-top">
              <span className="device-emoji">{u.deviceIcon}</span>
              <div>
                <h4>{u.device}</h4>
                <p className="mono text-dim">{u.ip}</p>
              </div>
              <span className={`badge ${st.cls}`}>{st.label}</span>
            </div>

            <div className="device-meta">
              <div className="meta-row">
                <span className="text-dim">Priority</span>
                <strong>{u.priority}</strong>
              </div>
              <div className="meta-row">
                <span className="text-dim">Allocated</span>
                <strong className="mono">{u.allocated} Mbps</strong>
              </div>
              <div className="meta-row">
                <span className="text-dim">Usage</span>
                <strong className="mono">{u.usage} Mbps</strong>
              </div>
            </div>

            <div className="progress-track">
              <div
                className="progress-fill"
                style={{ width: `${Math.round((u.usage / u.allocated) * 100)}%` }}
              />
            </div>

            <div className="device-signal">
              <SignalBars level={u.signal} />
              <span className={`signal-label sig-${u.signal}`}>
                📶 {u.signal.charAt(0).toUpperCase() + u.signal.slice(1)}
              </span>
            </div>

            <p className="text-dim" style={{ fontSize: 10, marginTop: 6 }}>
              Simulated profile · router/AP telemetry unavailable
            </p>
          </motion.div>
        );
      })}
    </div>
  );
}