import { useEffect, useState } from "react";
import { networkApi } from "../services/api";
import { SIMULATION, CALCULATED_FROM_REAL_DATA } from "../data/provenance";

export function useNetworkStats(pollMs = 2000) {
  const [stats, setStats] = useState({
    bandwidth: 0,
    latency: 0,
    packetLoss: 0,
    throughput: 0,
    jitter: 0,
    health: 0,
    healthLabel: "Poor",
    source: SIMULATION,
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
          setStats({
            bandwidth: Number(res.stats.bandwidth ?? 0),
            latency: Number(res.stats.latency ?? 0),
            packetLoss: Number(res.stats.packetLoss ?? 0),
            throughput: Number(res.stats.throughput ?? 0),
            jitter: Number(res.stats.jitter ?? 0),
            health: Number(res.stats.health ?? 0),
            healthLabel: res.stats.healthLabel || "Poor",
            source: res.source || SIMULATION,
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
