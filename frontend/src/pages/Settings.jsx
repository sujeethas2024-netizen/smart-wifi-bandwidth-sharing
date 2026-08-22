import { useState } from "react";
import { motion } from "framer-motion";
import { FiSave, FiSun, FiMoon, FiCheckCircle } from "react-icons/fi";
import { useTheme } from "../theme/ThemeContext";
import "../styles/pages.css";

const STRATEGIES = [
  { value: "nash", label: "Nash Equilibrium (Game Theory)", desc: "Stable strategy profile where no user benefits from deviating" },
  { value: "proportional", label: "Proportional Fair", desc: "Allocates proportional to demand while maximizing log utility" },
  { value: "priority", label: "Priority Based", desc: "High priority users get bandwidth first" },
  { value: "equal", label: "Equal Split", desc: "Divides bandwidth equally among all users" },
];

export default function Settings() {
  const { theme, toggleTheme } = useTheme();
  const [saved, setSaved] = useState(false);
  const [settings, setSettings] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("swbs-settings")) || {
        totalBandwidth: 100,
        maxUsers: 30,
        strategy: "nash",
        fairnessWeight: 0.7,
      };
    } catch {
      return { totalBandwidth: 100, maxUsers: 30, strategy: "nash", fairnessWeight: 0.7 };
    }
  });

  const update = (key, value) =>
    setSettings((s) => ({ ...s, [key]: value }));

  const handleSave = () => {
    localStorage.setItem("swbs-settings", JSON.stringify(settings));
    setSaved(true);
    setTimeout(() => setSaved(false), 2200);
  };

  return (
    <motion.div
      className="page"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="page-head">
        <div>
          <h2 className="page-title">⚙️ Settings</h2>
          <p className="text-dim">Configure network parameters and allocation behaviour</p>
        </div>
      </div>

      <div className="settings-grid">
        {/* Network params */}
        <motion.div className="glass settings-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <h3 className="section-title"><span className="dot" /> Network Parameters</h3>

          <label className="field">
            <span>Total Bandwidth (Mbps)</span>
            <input
              type="number"
              min="10"
              max="1000"
              value={settings.totalBandwidth}
              onChange={(e) => update("totalBandwidth", Number(e.target.value))}
            />
            <input
              type="range"
              min="10"
              max="500"
              step="5"
              value={settings.totalBandwidth}
              onChange={(e) => update("totalBandwidth", Number(e.target.value))}
            />
          </label>

          <label className="field">
            <span>Maximum Users</span>
            <input
              type="number"
              min="1"
              max="200"
              value={settings.maxUsers}
              onChange={(e) => update("maxUsers", Number(e.target.value))}
            />
            <input
              type="range"
              min="1"
              max="100"
              value={settings.maxUsers}
              onChange={(e) => update("maxUsers", Number(e.target.value))}
            />
          </label>

          <label className="field">
            <span>Fairness Weight ({settings.fairnessWeight.toFixed(2)})</span>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={settings.fairnessWeight}
              onChange={(e) => update("fairnessWeight", Number(e.target.value))}
            />
            <small className="text-dim">0 = pure efficiency · 1 = perfect equality</small>
          </label>
        </motion.div>

        {/* Strategy */}
        <motion.div className="glass settings-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <h3 className="section-title"><span className="dot" /> Allocation Strategy</h3>

          <div className="strategy-list">
            {STRATEGIES.map((s) => (
              <button
                key={s.value}
                className={`strategy-item ${settings.strategy === s.value ? "active" : ""}`}
                onClick={() => update("strategy", s.value)}
              >
                <span className="radio-dot" />
                <div>
                  <strong>{s.label}</strong>
                  <p className="text-dim">{s.desc}</p>
                </div>
              </button>
            ))}
          </div>
        </motion.div>

        {/* Appearance */}
        <motion.div className="glass settings-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <h3 className="section-title"><span className="dot" /> Appearance</h3>

          <div className="theme-picker">
            <button
              className={`theme-option ${theme === "light" ? "active" : ""}`}
              onClick={() => theme !== "light" && toggleTheme()}
            >
              <FiSun /> ☀️ Light
            </button>
            <button
              className={`theme-option ${theme === "dark" ? "active" : ""}`}
              onClick={() => theme !== "dark" && toggleTheme()}
            >
              <FiMoon /> 🌙 Dark
            </button>
          </div>

          <div className="palette-preview">
            {[["#2563eb", "Primary"], ["#14b8a6", "Secondary"], ["#7c3aed", "Accent"], ["#22c55e", "Success"], ["#ef4444", "Danger"]].map(
              ([c, n]) => (
                <div key={c} className="swatch">
                  <i style={{ background: c }} />
                  <span>{n}</span>
                </div>
              )
            )}
          </div>
        </motion.div>
      </div>

      <motion.button
        className="btn-gradient save-btn"
        onClick={handleSave}
        whileTap={{ scale: 0.97 }}
      >
        {saved ? <><FiCheckCircle /> Settings Saved!</> : <><FiSave /> Save Settings</>}
      </motion.button>
    </motion.div>
  );
}