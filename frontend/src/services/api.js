/* ============================================================
   API helper — talks to the Flask backend.
   Uses SAME-ORIGIN relative paths ("/api/..."). The Vite dev
   server proxies them to Flask on localhost:5000, so the app
   works on localhost AND from any phone/laptop on the same WiFi
   via http://<PC-IP>:5173 — no direct access to port 5000 or
   extra firewall rules required.
   ============================================================ */

export function apiBase() {
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

/* ---------------- Live network stats ---------------- */
export const networkApi = {
  stats: () => apiFetch("/api/network/stats"),
};