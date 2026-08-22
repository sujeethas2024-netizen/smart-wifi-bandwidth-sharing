import { useState, useRef, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { FiBell, FiSearch, FiSun, FiMoon, FiMenu, FiLogOut } from "react-icons/fi";
import { useTheme } from "../theme/ThemeContext";
import { NOTIFICATIONS } from "../data/mockData";
import { getCurrentUser, logout } from "../services/authService";
import "../styles/layout.css";

const TITLES = {
  "/dashboard": "Dashboard",
  "/users": "Connected Users",
  "/analytics": "Analytics",
  "/network": "Network Map",
  "/reports": "Reports",
  "/settings": "Settings",
  "/my-usage": "My Usage",
};

export default function Navbar({ onMenuClick }) {
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();
  const user = getCurrentUser();
  const [open, setOpen] = useState(false);
  const [read, setRead] = useState(false);
  const panelRef = useRef(null);

  const handleLogout = () => {
    logout();
    navigate("/", { replace: true });
  };

  useEffect(() => {
    const close = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  return (
    <motion.header
      className="navbar glass"
      initial={{ y: -60, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
    >
      <div className="nav-left">
        <button className="nav-burger" onClick={onMenuClick} aria-label="Menu">
          <FiMenu />
        </button>
        <h2 className="nav-title">{TITLES[location.pathname] || "Dashboard"}</h2>
      </div>

      <div className="nav-right">
        {/* Search */}
        <div className="nav-search">
          <FiSearch className="nav-search-icon" />
          <input type="text" placeholder="Search devices, users…" />
        </div>

        {/* Theme toggle */}
        <button
          className="nav-icon-btn"
          onClick={toggleTheme}
          aria-label="Toggle theme"
          title={theme === "dark" ? "Switch to Light ☀️" : "Switch to Dark 🌙"}
        >
          <AnimatePresence mode="wait" initial={false}>
            <motion.span
              key={theme}
              initial={{ rotate: -90, opacity: 0, scale: 0.6 }}
              animate={{ rotate: 0, opacity: 1, scale: 1 }}
              exit={{ rotate: 90, opacity: 0, scale: 0.6 }}
              transition={{ duration: 0.25 }}
            >
              {theme === "dark" ? <FiSun /> : <FiMoon />}
            </motion.span>
          </AnimatePresence>
        </button>

        {/* Notification bell */}
        <div className="nav-bell-wrap" ref={panelRef}>
          <button
            className="nav-icon-btn"
            onClick={() => {
              setOpen((o) => !o);
              setRead(true);
            }}
            aria-label="Notifications"
          >
            <FiBell />
            {!read && <span className="bell-dot" />}
          </button>

          <AnimatePresence>
            {open && (
              <motion.div
                className="notif-panel glass"
                initial={{ opacity: 0, y: -12, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -12, scale: 0.96 }}
                transition={{ duration: 0.22 }}
              >
                <div className="notif-head">
                  <strong>Notifications</strong>
                  <span className="notif-count">{NOTIFICATIONS.length} new</span>
                </div>
                <div className="notif-list">
                  {NOTIFICATIONS.map((n, i) => (
                    <motion.div
                      key={n.id}
                      className={`notif-item tone-${n.tone}`}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.06 }}
                    >
                      <span className="notif-icon">{n.icon}</span>
                      <div className="notif-body">
                        <p className="notif-title">{n.title}</p>
                        <p className="notif-text">{n.body}</p>
                        <span className="notif-time">{n.time}</span>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Logged-in user chip */}
        <div className="nav-user" title={`Logged in as ${user?.username || "guest"}`}>
          <span className="nav-user-avatar">{(user?.fullName || user?.username || "A").charAt(0).toUpperCase()}</span>
          <span className="nav-user-meta">
            <strong>{user?.fullName || user?.username || "Guest"}</strong>
            <small>{user?.role === "admin" ? "Administrator" : "Network User"}</small>
          </span>
        </div>

        {/* Logout */}
        <button
          className="nav-icon-btn nav-logout"
          onClick={handleLogout}
          aria-label="Logout"
          title="Logout"
        >
          <FiLogOut />
        </button>
      </div>
    </motion.header>
  );
}
