import { useDataMode } from "../hooks/useDataMode";

export default function ModeSwitcher() {
  const { mode, setMode } = useDataMode();

  return (
    <div className="mode-switcher" role="radiogroup" aria-label="Frontend data view">
      <button
        type="button"
        className={`mode-btn ${mode === "live" ? "active" : ""}`}
        onClick={() => setMode("live")}
        aria-pressed={mode === "live"}
      >
        🟢 LIVE SYSTEM
      </button>
      <button
        type="button"
        className={`mode-btn ${mode === "research" ? "active" : ""}`}
        onClick={() => setMode("research")}
        aria-pressed={mode === "research"}
      >
        🟠 RESEARCH SIMULATION
      </button>
    </div>
  );
}
