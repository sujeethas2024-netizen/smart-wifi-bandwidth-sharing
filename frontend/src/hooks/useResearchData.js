import { useEffect, useState, useMemo } from "react";
import { fetchResearchResults } from "../services/researchApi";

export function useResearchData(pollMs = Infinity) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let stop = false;
    const pull = async () => {
      try {
        const res = await fetchResearchResults();
        if (!stop && res?.ok && res.aggregated) {
          setData(res);
          setError("");
        } else if (!stop) {
          setError(res?.message || "Failed to load research data");
        }
      } catch {
        if (!stop) setError("Backend not reachable");
      } finally {
        if (!stop) setLoading(false);
      }
    };
    pull();
    if (pollMs !== Infinity && pollMs > 0) {
      const id = setInterval(pull, pollMs);
      return () => {
        stop = true;
        clearInterval(id);
      };
    }
    return () => {
      stop = true;
    };
  }, [pollMs]);

  const stats = useMemo(() => {
    if (!data?.aggregated?.length) return null;
    const rows = data.aggregated;
    const strategies = [...new Set(rows.map((r) => r.strategy))];
    const userCounts = [...new Set(rows.map((r) => r.number_of_users))].sort((a, b) => a - b);
    const latestByStrategy = {};
    for (const s of strategies) {
      const strategyRows = rows.filter((r) => r.strategy === s);
      const latestUserCount = Math.max(...strategyRows.map((r) => r.number_of_users));
      const latest = strategyRows.find((r) => r.number_of_users === latestUserCount);
      if (latest) latestByStrategy[s] = latest;
    }
    return {
      strategies,
      userCounts,
      latestByStrategy,
      totalRuns: data.raw_count || rows.length * 30,
      aggregatedCount: data.aggregated_count || rows.length,
    };
  }, [data]);

  return { data, stats, loading, error };
}
