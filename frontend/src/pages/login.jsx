import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  FiWifi, FiUser, FiLock, FiArrowRight, FiUserPlus,
  FiCheck, FiX, FiAtSign, FiFileText,
} from "react-icons/fi";
import {
  login,
  register,
  validateUsername,
  validatePassword,
  isUsernameAvailable,
  USAGE_REASONS,
} from "../services/authService";
import "../styles/login.css";

export default function Login() {
  const navigate = useNavigate();
  const [mode, setMode] = useState("login"); // "login" | "signup"

  // form state
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [usageReason, setUsageReason] = useState("");
  const [customReason, setCustomReason] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  /* Live validation */
  const unameCheck = useMemo(() => validateUsername(username), [username]);
  const passCheck = useMemo(() => validatePassword(password), [password]);

  /* Async username availability check (debounced) */
  const [unameAvailable, setUnameAvailable] = useState(null);
  useEffect(() => {
    if (mode !== "signup" || !username.trim()) {
      setUnameAvailable(null);
      return;
    }
    setUnameAvailable(null); // checking…
    const t = setTimeout(async () => {
      const available = await isUsernameAvailable(username);
      setUnameAvailable(available);
    }, 450);
    return () => clearTimeout(t);
  }, [username, mode]);

  const finalReason =
    usageReason === "Other" ? customReason.trim() : usageReason;

  const switchMode = (m) => {
    setMode(m);
    setError("");
    setSuccess("");
    setUsername("");
    setPassword("");
    setFullName("");
    setUsageReason("");
    setCustomReason("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (mode === "login") {
      if (!username || !password) {
        setError("Please enter both username and password");
        return;
      }
      setLoading(true);
      const res = await login(username, password);
      setLoading(false);
      if (res.ok) {
        navigate("/dashboard");
      } else {
        setError(res.error);
      }
      return;
    }

    // ---- Sign up ----
    if (!unameCheck.valid || unameAvailable === false) {
      setError("Please fix the username issues below.");
      return;
    }
    if (!passCheck.valid) {
      setError("Please satisfy all password requirements below.");
      return;
    }
    if (!finalReason || finalReason.length < 3) {
      setError("Please select or enter your WiFi usage reason.");
      return;
    }

    setLoading(true);
    const res = await register({
      username,
      password,
      fullName,
      usageReason: finalReason,
    });
    setLoading(false);

    if (!res.ok) {
      setError(res.error);
      return;
    }
    // Auto-login after successful registration
    const loginRes = await login(username, password);
    if (loginRes.ok) {
      setSuccess("Account created! Redirecting…");
      setTimeout(() => navigate("/dashboard"), 900);
    } else {
      switchMode("login");
      setError("Account created — please log in.");
    }
  };

  return (
    <div className="login-page">
      {/* Animated background */}
      <div className="login-blob b1" />
      <div className="login-blob b2" />
      <div className="login-blob b3" />

      <motion.div
        className="login-card glass"
        initial={{ opacity: 0, y: 40, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
      >
        {/* Animated WiFi illustration */}
        <div className="login-visual">
          <div className="wifi-rings">
            <span className="ring r1" />
            <span className="ring r2" />
            <span className="ring r3" />
            <div className="router-core">
              <FiWifi />
            </div>
          </div>
        </div>

        {/* University logo */}
        <div className="login-logo">
          <img
            src="/src/assets/logo.png"
            alt="University Logo"
            onError={(e) => { e.target.style.display = "none"; }}
          />
          <span className="logo-fallback">🎓</span>
        </div>

        <h1>Smart WiFi <span className="grad-text">Bandwidth Sharing</span></h1>
        <p className="login-sub">Game Theory based fair bandwidth allocation </p>

        {/* Mode tabs */}
        <div className="auth-tabs">
          <button
            type="button"
            className={mode === "login" ? "active" : ""}
            onClick={() => switchMode("login")}
          >
            <FiUser /> Login
          </button>
          <button
            type="button"
            className={mode === "signup" ? "active" : ""}
            onClick={() => switchMode("signup")}
          >
            <FiUserPlus /> Sign Up
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <AnimatePresence initial={false}>
            {mode === "signup" && (
              <motion.div
                key="fullname"
                className="input-wrap"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.25 }}
                style={{ overflow: "hidden" }}
              >
                <FiAtSign className="input-icon" />
                <input
                  type="text"
                  placeholder="Full name (optional)"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  maxLength={40}
                />
              </motion.div>
            )}
          </AnimatePresence>

          <div className="input-wrap">
            <FiUser className="input-icon" />
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              maxLength={16}
            />
          </div>

          {/* Username live feedback (signup) */}
          {mode === "signup" && username.length > 0 && (
            <div className={`rule-box ${unameAvailable === false ? "bad" : unameCheck.valid && unameAvailable ? "good" : ""}`}>
              {!unameCheck.valid ? (
                unameCheck.failed.map((r) => (
                  <p key={r.id} className="rule-line err"><FiX /> {r.label}</p>
                ))
              ) : unameAvailable === false ? (
                <p className="rule-line err">✖ Username “{username}” is already taken — try another.</p>
              ) : unameAvailable === null ? (
                <p className="rule-line dim">⏳ Checking availability…</p>
              ) : (
                <p className="rule-line ok"><FiCheck /> Username available!</p>
              )}
            </div>
          )}

          <div className="input-wrap">
            <FiLock className="input-icon" />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              maxLength={32}
            />
          </div>

          {/* Password rules checklist (signup) */}
          {mode === "signup" && password.length > 0 && (
            <motion.div
              className={`rule-box ${passCheck.valid ? "good" : ""}`}
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
            >
              {passCheck.results.map((r) => (
                <p key={r.id} className={`rule-line ${r.passed ? "ok" : "err"}`}>
                  {r.passed ? <FiCheck /> : <FiX />} {r.label}
                </p>
              ))}
            </motion.div>
          )}

          {/* Usage reason (signup — required) */}
          <AnimatePresence>
            {mode === "signup" && (
              <motion.div
                key="reason"
                className="reason-wrap"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.25 }}
                style={{ overflow: "hidden" }}
              >
                <label className="reason-label">
                  <FiFileText /> Reason for WiFi usage <span className="req">*</span>
                </label>
                <select
                  className="reason-select"
                  value={usageReason}
                  onChange={(e) => setUsageReason(e.target.value)}
                >
                  <option value="">— Select your primary usage —</option>
                  {USAGE_REASONS.map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>

                {usageReason === "Other" && (
                  <motion.input
                    initial={{ opacity: 0, y: -6 }}
                    animate={{ opacity: 1, y: 0 }}
                    type="text"
                    className="reason-custom"
                    placeholder="Describe your usage (min 3 characters)"
                    value={customReason}
                    onChange={(e) => setCustomReason(e.target.value)}
                    maxLength={80}
                  />
                )}
                <small className="text-dim reason-hint">
                  Shown to your network admin for fair bandwidth planning.
                </small>
              </motion.div>
            )}
          </AnimatePresence>

          {error && (
            <motion.p
              className="login-error"
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
            >
              ⚠️ {error}
            </motion.p>
          )}

          {success && (
            <motion.p
              className="login-success"
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
            >
              ✔ {success}
            </motion.p>
          )}

          <button type="submit" className="btn-gradient login-btn" disabled={loading}>
            {loading ? (
              <span className="mini-spinner dark" />
            ) : mode === "login" ? (
              <>Login <FiArrowRight /></>
            ) : (
              <>Create Account <FiUserPlus /></>
            )}
          </button>
        </form>

        <p className="login-hint text-dim">
          New user? Create your own account to get started.
        </p>
      </motion.div>
    </div>
  );
}