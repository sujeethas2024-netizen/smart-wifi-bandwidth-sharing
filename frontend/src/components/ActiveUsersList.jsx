import { FiUsers, FiClock, FiShield } from "react-icons/fi";
import "../styles/components.css";

export default function ActiveUsersList({ users, error, loading }) {
  return (
    <div className="chart-card glass">
      <div className="chart-head">
        <h3 className="section-title">
          <span className="dot" /> Active Users
          <strong className="active-users-count">
            {" "}
            {users.length}
          </strong>
        </h3>
        <FiUsers className="section-icon" />
      </div>

      <div className="card-body">
        {loading && <p className="text-dim">Refreshing…</p>}

        {error && (
          <p className="login-error">
            ⚠️ {error}
          </p>
        )}

        {!loading && !error && users.length === 0 && (
          <p className="text-dim">No active users</p>
        )}

        {!loading && users.length > 0 && (
          <div className="active-users-list">
            {users.map((u) => (
              <div key={u.username} className="active-user-row">
                <div className="user-info">
                  <span className="user-name">{u.fullName || u.username}</span>
                  <span className="user-username">@{u.username}</span>
                </div>
                <span className="user-role-badge">
                  <FiShield className="role-icon" /> {u.role}
                </span>
                <span className="user-last-seen" title={u.lastSeen}>
                  <FiClock className="clock-icon" /> {u.lastSeen}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
