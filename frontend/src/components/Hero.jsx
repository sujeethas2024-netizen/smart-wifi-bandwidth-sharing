import { motion } from "framer-motion";
import { FiWifi, FiPlay } from "react-icons/fi";

const FEATURES = [
  { icon: "🤖", text: "Game Theory Allocation" },
  { icon: "⚖️", text: "Fair Bandwidth Distribution" },
  { icon: "📡", text: "Local Network Monitoring" },
];

const FLOATERS = [
  { icon: <FiWifi />, top: "12%", left: "8%", size: 34, delay: 0 },
  { icon: <FiWifi />, top: "22%", left: "86%", size: 26, delay: 0.6 },
  { icon: <FiWifi />, top: "68%", left: "12%", size: 24, delay: 1.1 },
  { icon: <FiWifi />, top: "74%", left: "82%", size: 32, delay: 0.3 },
  { icon: <FiWifi />, top: "42%", left: "94%", size: 20, delay: 1.5 },
  { icon: <FiWifi />, top: "55%", left: "4%", size: 18, delay: 0.9 },
];

export default function Hero({ onStart }) {
  return (
    <motion.section
      className="hero glass"
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
    >
      {/* Animated gradient blobs */}
      <div className="hero-blob blob-1" />
      <div className="hero-blob blob-2" />
      <div className="hero-blob blob-3" />

      {/* Floating WiFi icons */}
      {FLOATERS.map((f, i) => (
        <span
          key={i}
          className="hero-floater"
          style={{
            top: f.top,
            left: f.left,
            fontSize: f.size,
            animationDelay: `${f.delay}s`,
          }}
        >
          {f.icon}
        </span>
      ))}

      <div className="hero-content">
        <motion.span
          className="hero-tag"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
        >
          ⚡ Game Theory · Nash Equilibrium Engine
        </motion.span>

        <motion.h1
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
        >
          Smart WiFi <span className="grad-text">Bandwidth Sharing</span>
        </motion.h1>

        <motion.p
          className="hero-sub"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.45, duration: 0.6 }}
        >
          Enterprise-grade network intelligence — allocate bandwidth through
          Nash equilibrium, monitor network performance, and keep every user happy.
        </motion.p>

        <motion.ul
          className="hero-features"
          initial="hidden"
          animate="show"
          variants={{ show: { transition: { staggerChildren: 0.15, delayChildren: 0.55 } } }}
        >
          {FEATURES.map((f) => (
            <motion.li
              key={f.text}
              variants={{ hidden: { opacity: 0, x: -16 }, show: { opacity: 1, x: 0 } }}
            >
              <span className="feat-check">✔</span> {f.icon} {f.text}
            </motion.li>
          ))}
        </motion.ul>

        <motion.div
          className="hero-cta"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.9 }}
        >
          <button className="btn-gradient hero-btn" onClick={onStart}>
            <FiPlay /> Start Monitoring
          </button>
          <span className="hero-live">
            <span className="pulse-dot" style={{ background: "#22c55e" }} />
            Network monitoring ready
          </span>
        </motion.div>
      </div>

      {/* Hero visual — animated router rings */}
      <div className="hero-visual">
        <div className="wifi-rings">
          <span className="ring r1" />
          <span className="ring r2" />
          <span className="ring r3" />
          <div className="router-core">
            <FiWifi />
          </div>
        </div>
      </div>
    </motion.section>
  );
}