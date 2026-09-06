import { useState, useEffect } from "react";

const MODE_KEY = "smart_wifi_data_mode";
const DEFAULT_MODE = "research";

export function useDataMode() {
  const [mode, setMode] = useState(() => {
    try {
      const stored = localStorage.getItem(MODE_KEY);
      return stored === "live" || stored === "research" ? stored : DEFAULT_MODE;
    } catch {
      return DEFAULT_MODE;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(MODE_KEY, mode);
    } catch {
      // ignore localStorage errors
    }
  }, [mode]);

  return {
    mode,
    setMode,
    isLive: mode === "live",
    isResearch: mode === "research",
  };
}
