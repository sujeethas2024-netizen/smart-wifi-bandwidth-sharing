/* ============================================================
   API helper — talks to the Flask backend.

   API base URL resolution order:
   1. Vite env var VITE_API_BASE (for public / split deployments)
   2. Runtime global __API_BASE__ (injected by backend in production)
   3. Empty string (same-origin / dev proxy)
   ============================================================ */

export function apiBase() {
  if (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_BASE) {
    return import.meta.env.VITE_API_BASE;
  }
  if (typeof globalThis !== "undefined" && globalThis.__API_BASE__) {
    return globalThis.__API_BASE__;
  }
  return "";
}

export async function apiFetch(path, options = {}, timeoutMs = 6000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${apiBase()}${path}`, {
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
      ...options,
    });
    clearTimeout(timer);
    return await res.json();
  } catch (err) {
    clearTimeout(timer);
    // Backend unreachable — caller decides on fallback behaviour
    return { ok: false, offline: true, error: "Backend not reachable" };
  }
}

/* ---------------- Auth endpoints ---------------- */
export const authApi = {
  register: (payload) =>
    apiFetch("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  login: (username, password) =>
    apiFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  checkUsername: (username) =>
    apiFetch(`/api/auth/check-username?username=${encodeURIComponent(username)}`),

  accounts: () => apiFetch("/api/auth/accounts"),

  me: (username) =>
    apiFetch(`/api/auth/me?username=${encodeURIComponent(username)}`),
};

/* ---------------- Experiment endpoints ---------------- */
export const experimentApi = {
  run: (config) =>
    apiFetch("/api/experiment/run", {
      method: "POST",
      body: JSON.stringify(config),
    }),

  runMultiSeed: (config) =>
    apiFetch("/api/experiment/run-multi-seed", {
      method: "POST",
      body: JSON.stringify(config),
    }),

  ablation: (config) =>
    apiFetch("/api/experiment/ablation", {
      method: "POST",
      body: JSON.stringify(config),
    }),

  sensitivity: (config) =>
    apiFetch("/api/experiment/sensitivity", {
      method: "POST",
      body: JSON.stringify(config),
    }),

  report: () => apiFetch("/api/experiment/report"),

  config: () => apiFetch("/api/experiment/config"),
};

/* ---------------- Live network data ---------------- */
export const networkApi = {
  stats: () => apiFetch("/api/network/stats"),
  users: () => apiFetch("/api/network/users"),
};
