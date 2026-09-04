import { useEffect, useState } from "react";
import { networkApi } from "../services/api";
import { SIMULATION, CALCULATED_FROM_REAL_DATA, UNAVAILABLE } from "../data/provenance";

export function useNetworkStats(pollMs = 2000) {
  const [stats, setStats] = useState({
    bandwidth: null,
    latency: null,
    packetLoss: null,
    throughput: null,
    jitter: null,
    health: null,
    healthLabel: "Unavailable",
    source: SIMULATION,
    liveMode: false,
    _meta: {},
  });
  const [history, setHistory] = useState({ labels: [], values: [] });
  const [live, setLive] = useState(false);

  useEffect(() => {
    let stop = false;
    const pull = async () => {
      try {
        const res = await networkApi.stats();
        if (!stop && res?.ok && res.stats) {
          const meta = res.stats._meta || {};
          const safeNum = (v) => (v === null || v === undefined ? null : Number(v));
          setStats({
            bandwidth: safeNum(res.stats.bandwidth),
            latency: safeNum(res.stats.latency),
            packetLoss: safeNum(res.stats.packetLoss),
            throughput: safeNum(res.stats.throughput),
            jitter: safeNum(res.stats.jitter),
            health: safeNum(res.stats.health),
            healthLabel: res.stats.healthLabel || "Unavailable",
            source: res.source || SIMULATION,
            liveMode: Boolean(res.live_mode),
            _meta: meta,
          });
          setLive(true);
          if (Array.isArray(res.history) && res.history.length > 0) {
            const now = Math.floor(Date.now() / 1000);
            const labels = res.history.map((h) => {
              const diff = now - (h.t || now);
              return diff <= 1 ? "now" : `-${diff}s`;
            });
            const values = res.history.map((h) => Number(h.v ?? 0));
            setHistory({ labels, values });
          }
        }
      } catch {
        // keep last known data when backend is unreachable
      }
    };
    pull();
    const id = setInterval(pull, pollMs);
    return () => {
      stop = true;
      clearInterval(id);
    };
  }, [pollMs]);

  return { stats, history, live };
}
