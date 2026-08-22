import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { FiGrid, FiList, FiDatabase, FiRefreshCw } from "react-icons/fi";
import UserTable from "../components/UserTable";
import DeviceCards from "../components/DeviceCards";
import { generateUsers, generateStats, tickUsers } from "../data/mockData";
import { fetchAccounts } from "../services/authService";
import "../styles/pages.css";

/* Registered accounts from the backend database (SQLite) */
function AccountsPanel() {
  const [data, setData] = useState({ source: null, accounts: [] });
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    const res = await fetchAccounts();
    setData(res);
    setLoading(false);
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 15000); // refresh every 15s
    return () => clearInterval(id);
  }, []);

  return (
    <div className="chart-card glass">
      <div className="chart-head">
        <h3 className="section-title">
          <span className="dot" /> <FiDatabase /> Registered Accounts
          <span className={`db-chip ${data.source === "server" ? "on" : ""}`}>
            {loading
              ? "Loading…"
              : data.source === "server"
              ? "● Live from Database"
              : "○ Offline mirror"}
          </span>
        </h3>
        <button className="btn-ghost refresh-btn" onClick={load}>
          <FiRefreshCw /> Refresh
        </button>
      </div>

      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>User</th>
              <th>Role</th>
              <th>Reason for WiFi Usage</th>
              <th>Devices</th>
              <th>Registered</th>
              <th>Last Login</th>
            </tr>
          </thead>
          <tbody>
            {data.accounts.map((a, i) => (
              <motion.tr
                key={a.username}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: Math.min(i * 0.05, 0.5) }}
              >
                <td>
                  <div className="cell-user">
                    <span className="user-avatar">{(a.full_name || a.username || "?").charAt(0).toUpperCase()}</span>
                    <div>
                      <p className="cell-name">{a.full_name || a.username}</p>
                      <p className="cell-sub mono">@{a.username}</p>
                    </div>
                  </div>
                </td>
                <td>
                  <span className={`badge ${a.role === "admin" ? "badge-accent" : "badge-info"}`}>
                    {a.role === "admin" ? "🛡️ Admin" : "👤 User"}
                  </span>
                </td>
                <td><span className="reason-badge">📋 {a.usage_reason || a.usageReason || "—"}</span></td>
                <td>{a.device_count ?? a.deviceCount ?? 1}</td>
                <td className="mono text-dim">
                  {a.created_at ? new Date(a.created_at).toLocaleDateString() : "—"}
                </td>
                <td className="mono text-dim">
                  {a.last_login ? new Date(a.last_login).toLocaleString() : "Never"}
                </td>
              </motion.tr>
            ))}
            {!loading && data.accounts.length === 0 && (
              <tr><td colSpan="6" className="empty-row">No registered accounts yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function Users() {
  const [users, setUsers] = useState(() => generateUsers());
  const [view, setView] = useState("table");

  useEffect(() => {
    const id = setInterval(() => setUsers((prev) => tickUsers(prev)), 3000);
    return () => clearInterval(id);
  }, []);

  const stats = useMemo(() => generateStats(users), [users]);

  return (
    <motion.div
      className="page"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="page-head">
        <div>
          <h2 className="page-title">👥 Connected Users</h2>
          <p className="text-dim">
            {stats.connectedUsers} online · {stats.totalUsers} total registered devices
          </p>
        </div>

        <div className="view-toggle glass">
          <button
            className={view === "table" ? "active" : ""}
            onClick={() => setView("table")}
          >
            <FiList /> Table
          </button>
          <button
            className={view === "cards" ? "active" : ""}
            onClick={() => setView("cards")}
          >
            <FiGrid /> Cards
          </button>
        </div>
      </div>

      {/* Status summary */}
      <div className="status-summary">
        <span className="badge badge-success">🟢 Online {users.filter((u) => u.status === "online").length}</span>
        <span className="badge badge-warning">🟡 Idle {users.filter((u) => u.status === "idle").length}</span>
        <span className="badge badge-danger">🔴 Offline {users.filter((u) => u.status === "offline").length}</span>
      </div>

      {view === "table" ? (
        <UserTable users={users} />
      ) : (
        <DeviceCards users={users} />
      )}

      {/* Real accounts from the backend database */}
      <AccountsPanel />
    </motion.div>
  );
}