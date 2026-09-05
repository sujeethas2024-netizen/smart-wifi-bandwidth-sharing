import { useState, useEffect } from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";

import Login from "./pages/login";
import Dashboard from "./pages/Dashboard";           // Admin dashboard
import UserDashboard from "./pages/UserDashboard";   // User portal home
import MyUsage from "./pages/MyUsage";               // User personal usage
import Users from "./pages/Users";
import Analytics from "./pages/Analytics";
import Network from "./pages/Network";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";
import ResearchExperiment from "./pages/ResearchExperiment"; // Research experiments

import Sidebar from "./components/Sidebar";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";

import { getCurrentUser, startHeartbeat } from "./services/authService";

import "./styles/layout.css";
import "./styles/components.css";
import "./styles/pages.css";

/* Redirects to login when no active session */
function RequireAuth({ children }) {
  const user = getCurrentUser();
  if (!user) return <Navigate to="/" replace />;
  return children;
}

/* Admin-only wrapper — users are bounced to their own dashboard */
function AdminOnly({ children }) {
  const user = getCurrentUser();
  if (!user) return <Navigate to="/" replace />;
  if (user.role !== "admin") return <Navigate to="/dashboard" replace />;
  return children;
}

/* User-only wrapper — admins are bounced to the admin console */
function UserOnly({ children }) {
  const user = getCurrentUser();
  if (!user) return <Navigate to="/" replace />;
  if (user.role === "admin") return <Navigate to="/analytics" replace />;
  return children;
}

function DashboardLayout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  const user = getCurrentUser();
  const isAdmin = user?.role === "admin";

  return (
    <div className="app-shell">
      <Sidebar />
      {/* Mobile drawer backdrop */}
      {menuOpen && (
        <div className="drawer-backdrop" onClick={() => setMenuOpen(false)} />
      )}

      <div className="app-main">
        <Navbar onMenuClick={() => setMenuOpen((o) => !o)} />

        <AnimatePresence mode="wait">
          <motion.main
            key={location.pathname}
            className="app-content"
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
          >
            <Routes location={location}>
              {/* Role-aware home */}
              <Route
                path="/dashboard"
                element={isAdmin ? <Dashboard /> : <UserDashboard />}
              />

              {/* Admin-only pages */}
              <Route path="/users" element={<AdminOnly><Users /></AdminOnly>} />
              <Route path="/analytics" element={<AdminOnly><Analytics /></AdminOnly>} />
              <Route path="/reports" element={<AdminOnly><Reports /></AdminOnly>} />
              <Route path="/settings" element={<AdminOnly><Settings /></AdminOnly>} />
              <Route path="/research" element={<AdminOnly><ResearchExperiment /></AdminOnly>} />

              {/* User-only page */}
              <Route path="/my-usage" element={<UserOnly><MyUsage /></UserOnly>} />

              {/* Shared (read-only for users) */}
              <Route path="/network" element={<Network />} />

              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>

            <Footer />
          </motion.main>
        </AnimatePresence>
      </div>
    </div>
  );
}

function App() {
  useEffect(() => {
    startHeartbeat();
  }, []);

  return (
    <Routes>
      <Route path="/" element={<Login />} />
      <Route
        path="/*"
        element={
          <RequireAuth>
            <DashboardLayout />
          </RequireAuth>
        }
      />
    </Routes>
  );
}

export default App;