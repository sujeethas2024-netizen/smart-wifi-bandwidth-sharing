import { useEffect, useState } from "react";
import { networkApi } from "../services/api";
import { UNAVAILABLE } from "../data/provenance";

const EMPTY_META = Object.freeze({
  bandwidth_source: UNAVAILABLE,
  latency_source: UNAVAILABLE,
  packetLoss_source: UNAVAILABLE,
  throughput_source: UNAVAILABLE,
  jitter_source: UNAVAILABLE,
  health_source: UNAVAILABLE,
});

export const EMPTY_NETWORK_STATS = Object.freeze({
  bandwidth: null,
  latency: null,
  packetLoss: null,
  throughput: null,
  jitter: null,
  health: null,
  healthLabel: "Unavailable",
  source: UNAVAILABLE,
  liveMode: false,
  _meta: EMPTY_META,
});

export function useNetworkStats(pollMs = 2000) {
  const [stats, setStats] = useState(EMPTY_NETWORK_STATS);
  const [history, setHistory] = useState({ labels: [], values: [] });
  const [live, setLive] = useState(false);

  useEffect(() => {
    let stop = false;
    const pull = async () => {
      try {
        const res = await networkApi.stats();
        if (!stop && res?.ok && res.stats) {
          const meta = { ...(res.stats._meta || {}) };
          if (meta.packet_loss_source && !meta.packetLoss_source) {
            meta.packetLoss_source = meta.packet_loss_source;
          }
          const safeNum = (v) => {
            if (v === null || v === undefined || v === "") return null;
            const value = Number(v);
            return Number.isFinite(value) ? value : null;
          };
          setStats({
            bandwidth: safeNum(res.stats.bandwidth),
            latency: safeNum(res.stats.latency),
            packetLoss: safeNum(res.stats.packetLoss),
            throughput: safeNum(res.stats.throughput),
            jitter: safeNum(res.stats.jitter),
            health: safeNum(res.stats.health),
            healthLabel: res.stats.healthLabel || "Unavailable",
            source: res.source || UNAVAILABLE,
            liveMode: Boolean(res.live_mode),
            _meta: meta,
          });
          setLive(Boolean(res.live_mode));
          if (Array.isArray(res.history) && res.history.length > 0) {
            const now = Math.floor(Date.now() / 1000);
            const labels = res.history.map((h) => {
              const diff = now - (h.t || now);
              return diff <= 1 ? "now" : `-${diff}s`;
            });
            const values = res.history.map((h) => safeNum(h.v) ?? 0);
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
