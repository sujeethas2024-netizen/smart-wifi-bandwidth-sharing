/* ============================================================
   Auth service — talks to the Flask backend (SQLite accounts DB).
   Falls back to a local mirror in localStorage when the backend
   is unreachable, so the demo always works offline too.
   ============================================================ */

import { authApi, apiBase } from "./api";

const MIRROR_KEY = "swbs-accounts";     // offline fallback mirror
const SESSION_KEY = "swbs-session";

/* ---------------- Heartbeat lifecycle ---------------- */
const HEARTBEAT_INTERVAL = 30000; // ~30 seconds
let heartbeatTimerId = null;

/* ---------------- Validation patterns ---------------- */
export const USERNAME_RULES = [
  { id: "length", label: "4–16 characters", test: (v) => v.length >= 4 && v.length <= 16 },
  { id: "start", label: "Starts with a letter", test: (v) => /^[a-zA-Z]/.test(v) },
  { id: "chars", label: "Only letters, numbers & underscore", test: (v) => /^[a-zA-Z0-9_]*$/.test(v) },
];

export const PASSWORD_RULES = [
  { id: "length", label: "At least 8 characters", test: (v) => v.length >= 8 },
  { id: "upper", label: "One uppercase letter (A–Z)", test: (v) => /[A-Z]/.test(v) },
  { id: "lower", label: "One lowercase letter (a–z)", test: (v) => /[a-z]/.test(v) },
  { id: "digit", label: "One number (0–9)", test: (v) => /\d/.test(v) },
  { id: "special", label: "One special character (@$!%*?&#)", test: (v) => /[@$!%*?&#]/.test(v) },
];

export const USERNAME_PATTERN = /^[a-zA-Z][a-zA-Z0-9_]{3,15}$/;
export const PASSWORD_PATTERN =
  /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[^\s]{8,32}$/;

/* Declared WiFi usage reasons — stored per account & shown to admin */
export const USAGE_REASONS = [
  "Online Classes / Study",
  "Work From Home",
  "Video Streaming",
  "Online Gaming",
  "Video Conferencing",
  "Social Media",
  "Software Downloads",
  "Smart Home Devices",
  "General Browsing",
  "Other",
];

export function validateUsername(username) {
  const failed = USERNAME_RULES.filter((r) => !r.test(username || ""));
  return { valid: failed.length === 0, failed };
}

export function validatePassword(password) {
  const results = PASSWORD_RULES.map((r) => ({
    ...r,
    passed: r.test(password || ""),
  }));
  return { valid: results.every((r) => r.passed), results };
}

/* ---------------- Offline mirror helpers ---------------- */
function readMirror() {
  try {
    return JSON.parse(localStorage.getItem(MIRROR_KEY)) || [];
  } catch {
    return [];
  }
}

function writeMirror(accounts) {
  localStorage.setItem(MIRROR_KEY, JSON.stringify(accounts));
}

function hash(str) {
  let h1 = 0xdeadbeef;
  let h2 = 0x41c6ce57;
  for (let i = 0; i < str.length; i++) {
    const ch = str.charCodeAt(i);
    h1 = Math.imul(h1 ^ ch, 2654435761);
    h2 = Math.imul(h2 ^ ch, 1597334677);
  }
  h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
  h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
  return (h2 >>> 0).toString(16).padStart(8, "0") + (h1 >>> 0).toString(16).padStart(8, "0");
}

function mirrorUpsert(account) {
  const accounts = readMirror();
  const idx = accounts.findIndex(
    (a) => a.username.toLowerCase() === account.username.toLowerCase()
  );
  if (idx >= 0) accounts[idx] = { ...accounts[idx], ...account };
  else accounts.push(account);
  writeMirror(accounts);
}

/* Seed local admin so offline demo still works */
(function seedMirrorAdmin() {
  const accounts = readMirror();
  if (!accounts.some((a) => a.username === "admin")) {
    accounts.push({
      username: "admin",
      fullName: "Administrator",
      passHash: hash("Admin@123"),
      role: "admin",
      usageReason: "Network Administration",
      createdAt: new Date().toISOString(),
    });
    writeMirror(accounts);
  }
})();

/* ---------------- Session ---------------- */
export function setSession(user, sessionId) {
  const payload = { user: user || null, sessionId: sessionId || null };
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(payload));
}

export function getCurrentUser() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === "object" && "user" in parsed) {
      return parsed.user;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function getSessionId() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === "object" && "sessionId" in parsed) {
      return parsed.sessionId || null;
    }
    return null;
  } catch {
    return null;
  }
}

export async function logout() {
  stopHeartbeat();
  const sid = getSessionId();
  // Always clear the local session, even if the server call fails —
  // the user must not remain "logged in" merely because the server
  // is unreachable.
  sessionStorage.removeItem(SESSION_KEY);
  if (!sid) {
    return { ok: true, status: "signed_out" };
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 6000);
  try {
    const res = await fetch(`${apiBase()}/api/auth/logout`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${sid}`,
      },
      signal: controller.signal,
    });
    clearTimeout(timer);
    return await res.json();
  } catch (err) {
    clearTimeout(timer);
    return { ok: false, offline: true, error: "Backend not reachable" };
  }
}

/* ---------------- Authenticated heartbeat ---------------- */

/**
 * Internal handler for heartbeat results.
 * - 401 (unauthorized) → stop the timer and clear the local session.
 * - Network errors (offline) → keep the session; the next scheduled
 *   heartbeat attempt will retry.
 */
function handleHeartbeatResult(res) {
  if (res && res.unauthorized) {
    stopHeartbeat();
    setSession(null, null);
  }
}

/**
 * Stop the automatic heartbeat timer.
 * Safe to call when no timer is running (idempotent).
 */
export function stopHeartbeat() {
  if (heartbeatTimerId !== null) {
    clearInterval(heartbeatTimerId);
    heartbeatTimerId = null;
  }
}

/**
 * Start the automatic heartbeat lifecycle.
 *
 * - Sends one immediate heartbeat right away.
 * - Schedules a follow-up heartbeat every HEARTBEAT_INTERVAL (≈30 s).
 * - Does nothing (returns false) when there is no valid session ID or
 *   when a timer is already running (prevents duplicates).
 *
 * Returns `true` if the lifecycle was started.
 */
export function startHeartbeat() {
  const sid = getSessionId();
  if (!sid) {
    return false;
  }
  if (heartbeatTimerId !== null) {
    return false;
  }
  heartbeat()
    .then(handleHeartbeatResult)
    .catch(() => {});
  heartbeatTimerId = setInterval(() => {
    heartbeat().then(handleHeartbeatResult).catch(() => {});
  }, HEARTBEAT_INTERVAL);
  return true;
}

/**
 * Send an authenticated heartbeat to the backend.
 * Uses the stored session ID and Authorization: Bearer header.
 * Returns { ok:true, status, lastSeen } on success or
 *         { ok:false, offline?, error } on failure / missing session.
 * On HTTP 401 the result is tagged with `unauthorized: true` so the
 * heartbeat lifecycle can tear down the local session.
 */
export async function heartbeat() {
  const sid = getSessionId();
  if (!sid) {
    return { ok: false, error: "No active session." };
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 6000);
  try {
    const res = await fetch(`${apiBase()}/api/auth/heartbeat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${sid}`,
      },
      signal: controller.signal,
    });
    clearTimeout(timer);
    const data = await res.json();
    if (res.status === 401) {
      return { ...data, unauthorized: true };
    }
    return data;
  } catch (err) {
     clearTimeout(timer);
    return { ok: false, offline: true, error: "Backend not reachable" };
  }
}

/* ---------------- Active-users API ---------------- */

/**
 * Fetch the server-authoritative list of currently active users.
 * Uses getSessionId() + Authorization: Bearer header — same pattern
 * as heartbeat() and logout().
 *
 * Returns the parsed JSON on success: { ok:true, count, users }
 * On HTTP 401 → { ok:false, unauthorized:true, ... }
 * On network error → { ok:false, offline:true, error }
 */
export async function fetchActiveUsers() {
  const sid = getSessionId();
  if (!sid) {
    return { ok: false, offline: true, error: "No active session." };
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 6000);
  try {
    const res = await fetch(`${apiBase()}/api/auth/active-users`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${sid}`,
      },
      signal: controller.signal,
    });
    clearTimeout(timer);
    const data = await res.json();
    if (res.status === 401) {
      return { ...data, unauthorized: true };
    }
    return data;
  } catch (err) {
    clearTimeout(timer);
    return { ok: false, offline: true, error: "Backend not reachable" };
  }
}

/* ---------------- Public async API ---------------- */

/**
 * Register via backend → SQLite. Mirrors locally as fallback.
 * Returns { ok } | { ok:false, error }.
 */
export async function register({ username, password, fullName, usageReason }) {
  const uname = (username || "").trim();

  if (!USERNAME_PATTERN.test(uname)) {
    return { ok: false, error: "Username does not match the required pattern." };
  }
  if (!PASSWORD_PATTERN.test(password || "")) {
    return { ok: false, error: "Password does not meet all requirements." };
  }
  if (!usageReason || usageReason.trim().length < 3) {
    return { ok: false, error: "Please select or enter your WiFi usage reason." };
  }

  // Try backend first
  const res = await authApi.register({
    username: uname,
    password,
    fullName,
    usageReason: usageReason.trim(),
  });

  if (!res.offline) {
    if (res.ok) {
      return { ok: true, user: res.user };
    }
    return { ok: false, error: res.error || "Registration failed." };
  }

  // ---- Offline fallback (localStorage mirror) ----
  const accounts = readMirror();
  if (accounts.some((a) => a.username.toLowerCase() === uname.toLowerCase())) {
    return { ok: false, error: `Username "${uname}" is already taken.` };
  }
  const account = {
    username: uname,
    fullName: (fullName || uname).trim().slice(0, 40),
    passHash: hash(password),
    role: "user",
    usageReason: usageReason.trim(),
    createdAt: new Date().toISOString(),
  };
  accounts.push(account);
  writeMirror(accounts);
  return { ok: true, user: publicView(account) };
}

/**
 * Login via backend → SQLite. Falls back to the local mirror.
 * Returns { ok, user } | { ok:false, error }.
 */
export async function login(username, password) {
  const uname = (username || "").trim();

  const res = await authApi.login(uname, password);

  if (!res.offline) {
    if (res.ok) {
      setSession(res.user, res.sessionId);
      if (res.sessionId) {
        startHeartbeat();
      }
      return { ok: true, user: res.user, sessionId: res.sessionId };
    }
    return { ok: false, error: res.error || "Login failed." };
  }

  // ---- Offline fallback ----
  const account = readMirror().find(
    (a) => a.username.toLowerCase() === uname.toLowerCase()
  );
  if (!account) {
    return { ok: false, error: "No account found with this username." };
  }
  if (account.passHash !== hash(password)) {
    return { ok: false, error: "Incorrect password. Please try again." };
  }
  const user = publicView(account);
  setSession(user, null);
  return { ok: true, user, sessionId: null };
}

/** Live username availability from backend (falls back to mirror). */
export async function isUsernameAvailable(username) {
  const uname = (username || "").trim();
  if (!uname) return true;

  const res = await authApi.checkUsername(uname);
  if (!res.offline && typeof res.available === "boolean") {
    return res.available;
  }
  return !readMirror().some(
    (a) => a.username.toLowerCase() === uname.toLowerCase()
  );
}

/** Registered accounts (admin view). Backend first, mirror fallback. */
export async function fetchAccounts() {
  const res = await authApi.accounts();
  if (!res.offline && res.ok) {
    return { source: "server", accounts: res.accounts };
  }
  return {
    source: "local",
    accounts: readMirror().map((a) => ({
      username: a.username,
      full_name: a.fullName,
      role: a.role,
      usage_reason: a.usageReason || "—",
      created_at: a.createdAt,
      last_login: null,
    })),
  };
}

export function listUsernames() {
  return readMirror().map((a) => a.username);
}

function publicView(account) {
  return {
    username: account.username,
    fullName: account.fullName || account.full_name,
    role: account.role,
    usageReason: account.usageReason || account.usage_reason,
    deviceCount: account.deviceCount || account.device_count || 1,
    createdAt: account.createdAt || account.created_at,
  };
}