import { NavLink, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  FiHome,
  FiUsers,
  FiBarChart2,
  FiSettings,
  FiFileText,
  FiWifi,
  FiLogOut,
  FiActivity,
} from "react-icons/fi";
import { logout, getCurrentUser } from "../services/authService";
import "../styles/layout.css";

const ADMIN_LINKS = [
  { to: "/dashboard", icon: <FiHome />, label: "Dashboard" },
  { to: "/users", icon: <FiUsers />, label: "Users" },
  { to: "/analytics", icon: <FiBarChart2 />, label: "Analytics" },
  { to: "/network", icon: <FiWifi />, label: "Network" },
  { to: "/reports", icon: <FiFileText />, label: "Reports" },
  { to: "/settings", icon: <FiSettings />, label: "Settings" },
];

const USER_LINKS = [
  { to: "/dashboard", icon: <FiHome />, label: "My Dashboard" },
  { to: "/my-usage", icon: <FiActivity />, label: "My Usage" },
  { to: "/network", icon: <FiWifi />, label: "Network Status" },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const user = getCurrentUser();
  const isAdmin = user?.role === "admin";
  const links = isAdmin ? ADMIN_LINKS : USER_LINKS;

  const handleLogout = () => {
    logout();
    navigate("/", { replace: true });
  };

  return (
    <motion.aside
      className="sidebar"
      initial={{ x: -80, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
    >
      {/* Logo */}
      <div className="side-logo">
        <span className="logo-icon">
          <FiWifi />
        </span>
        <span className="logo-text">Smart WiFi</span>
      </div>

      {/* Role chip */}
      <div className="side-role">
        <span className={`role-pill ${isAdmin ? "role-admin" : "role-user"}`}>
          {isAdmin ? "🛡️ Admin" : "👤 User"}
        </span>
      </div>

      {/* Nav links */}
      <nav className="side-nav">
        {links.map((l, i) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.to === "/dashboard"}
            className={({ isActive }) =>
              `side-link ${isActive ? "active" : ""}`
            }
            style={{ transitionDelay: `${i * 30}ms` }}
          >
            <span className="side-icon">{l.icon}</span>
            <span className="side-label">{l.label}</span>
            <span className="side-tooltip">{l.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Logout */}
      <button className="side-link side-logout" onClick={handleLogout}>
        <span className="side-icon">
          <FiLogOut />
        </span>
        <span className="side-label">Logout</span>
        <span className="side-tooltip">Logout</span>
      </button>
    </motion.aside>
  );
}