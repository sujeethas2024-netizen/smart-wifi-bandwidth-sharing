import { motion } from "framer-motion";
import "../styles/components.css";

/**
 * Animated network topology:
 *   Internet → Main Router → { Laptop, Mobile, TV, ... }
 * Lines carry animated "data packets" via SVG dash animation.
 */
export default function NetworkTopology({ users }) {
  // Pick up to 6 representative device nodes
  const nodes = users.slice(0, 6);
  const W = 760;
  const H = 380;
  const internetX = W / 2;
  const routerY = 150;
  const nodeY = 320;

  const positions = nodes.map((_, i) => {
    const spacing = W / (nodes.length + 1);
    return { x: spacing * (i + 1), y: nodeY };
  });

  return (
    <div className="topology glass">
      <h3 className="section-title"><span className="dot" /> Network Topology</h3>

      <svg viewBox={`0 0 ${W} ${H}`} className="topo-svg">
        <defs>
          <linearGradient id="linkGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2563eb" />
            <stop offset="100%" stopColor="#14b8a6" />
          </linearGradient>
        </defs>

        {/* Internet → Router link */}
        <line
          x1={internetX} y1="70" x2={internetX} y2={routerY - 26}
          stroke="url(#linkGrad)" strokeWidth="2.5"
          strokeDasharray="8 6" className="flow-line"
        />

        {/* Router → Device links */}
        {positions.map((p, i) => (
          <g key={i}>
            <path
              d={`M ${internetX} ${routerY + 24} C ${internetX} ${(routerY + p.y) / 2}, ${p.x} ${(routerY + p.y) / 2}, ${p.x} ${p.y - 30}`}
              fill="none"
              stroke="url(#linkGrad)"
              strokeWidth="2"
              opacity={nodes[i].status === "offline" ? 0.25 : 0.75}
              strokeDasharray="7 5"
              className="flow-line"
            />
            {/* travelling packet */}
            {nodes[i].status !== "offline" && (
              <circle r="4" fill="#22c55e" className="packet">
                <animateMotion
                  dur={`${2 + (i % 3) * 0.6}s`}
                  repeatCount="indefinite"
                  path={`M ${internetX} ${routerY + 24} C ${internetX} ${(routerY + p.y) / 2}, ${p.x} ${(routerY + p.y) / 2}, ${p.x} ${p.y - 30}`}
                />
              </circle>
            )}
          </g>
        ))}

        {/* Internet node */}
        <motion.g
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
          style={{ transformOrigin: `${internetX}px 40px` }}
        >
          <circle cx={internetX} cy="40" r="28" fill="rgba(124,58,237,0.18)" stroke="#7c3aed" strokeWidth="2" className="pulse-ring" />
          <text x={internetX} y="36" textAnchor="middle" fontSize="20">🌐</text>
          <text x={internetX} y="52" textAnchor="middle" fontSize="9" fill="var(--text-dim)">Internet</text>
        </motion.g>

        {/* Router node */}
        <motion.g
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.45, type: "spring", stiffness: 200 }}
          style={{ transformOrigin: `${internetX}px ${routerY}px` }}
        >
          <rect
            x={internetX - 62} y={routerY - 24} width="124" height="48" rx="12"
            fill="rgba(37,99,235,0.18)" stroke="#2563eb" strokeWidth="2"
          />
          <text x={internetX} y={routerY - 4} textAnchor="middle" fontSize="13">📡</text>
          <text x={internetX} y={routerY + 14} textAnchor="middle" fontSize="10" fontWeight="700" fill="var(--text)">
            Main Router
          </text>
        </motion.g>

        {/* Device nodes */}
        {positions.map((p, i) => {
          const u = nodes[i];
          const color =
            u.status === "online" ? "#22c55e" : u.status === "idle" ? "#f59e0b" : "#ef4444";
          return (
            <motion.g
              key={u.id}
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.65 + i * 0.1, type: "spring", stiffness: 220 }}
              style={{ transformOrigin: `${p.x}px ${p.y}px` }}
            >
              <circle cx={p.x} cy={p.y} r="26" fill="rgba(20,184,166,0.15)" stroke={color} strokeWidth="2" />
              <text x={p.x} y={p.y + 5} textAnchor="middle" fontSize="17">{u.deviceIcon}</text>
              <text x={p.x} y={p.y + 44} textAnchor="middle" fontSize="10" fill="var(--text)">{u.device}</text>
              <text x={p.x} y={p.y + 57} textAnchor="middle" fontSize="8.5" fill="var(--text-dim)" className="mono">{u.ip}</text>
              <circle cx={p.x + 19} cy={p.y - 19} r="5" fill={color} className="pulse-dot" />
            </motion.g>
          );
        })}
      </svg>

      <div className="topo-legend">
        <span><i style={{ background: "#22c55e" }} /> Online</span>
        <span><i style={{ background: "#f59e0b" }} /> Idle</span>
        <span><i style={{ background: "#ef4444" }} /> Offline</span>
      </div>
    </div>
  );
}