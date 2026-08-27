import { motion } from "framer-motion";
import "../styles/components.css";

function strengthColor(s) {
  if (s >= 85) return "#22c55e";
  if (s >= 70) return "#14b8a6";
  if (s >= 55) return "#f59e0b";
  return "#ef4444";
}

function strengthLabel(s) {
  if (s >= 85) return "Excellent";
  if (s >= 70) return "Good";
  if (s >= 55) return "Fair";
  return "Weak";
}

export default function CoverageMap({ rooms = [] }) {
  return (
    <div className="coverage glass">
      <h3 className="section-title"><span className="dot" /> WiFi Coverage Map</h3>

      {/* Home layout */}
      <div className="home-layout">
        {/* Router in the middle */}
        <motion.div
          className="home-router"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 200, delay: 0.3 }}
        >
          <span className="router-pulse" />
          📡
          <small>Router</small>
        </motion.div>

        {rooms.map((room, i) => {
          const color = strengthColor(room.strength);
          return (
            <motion.div
              key={room.name}
              className={`room room-${i}`}
              initial={{ opacity: 0, scale: 0.85 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.15 + i * 0.12, duration: 0.45 }}
              whileHover={{ scale: 1.04 }}
              style={{ borderColor: `${color}66` }}
            >
              <div className="room-head">
                <span className="room-icon">{room.icon}</span>
                <strong>{room.name}</strong>
              </div>

              {/* Signal strength bar */}
              <div className="room-signal">
                <div className="progress-track">
                  <motion.div
                    className="progress-fill"
                    initial={{ width: 0 }}
                    animate={{ width: `${room.strength}%` }}
                    transition={{ delay: 0.5 + i * 0.12, duration: 0.9, ease: "easeOut" }}
                    style={{ background: `linear-gradient(90deg, ${color}88, ${color})` }}
                  />
                </div>
                <div className="room-signal-meta">
                  <span style={{ color }}>📶 {strengthLabel(room.strength)}</span>
                  <span className="mono text-dim">{room.strength}%</span>
                </div>
              </div>

              <span className="room-devices">{room.devices} devices</span>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}