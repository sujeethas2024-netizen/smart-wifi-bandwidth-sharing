import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FiSearch, FiChevronLeft, FiChevronRight } from "react-icons/fi";
import "../styles/components.css";

const PAGE_SIZE = 6;

function StatusBadge({ status }) {
  const map = {
    online: { cls: "badge-success", label: "🟢 Online" },
    idle: { cls: "badge-warning", label: "🟡 Idle" },
    offline: { cls: "badge-danger", label: "🔴 Offline" },
  };
  const s = map[status] || map.offline;
  return <span className={`badge ${s.cls}`}>{s.label}</span>;
}

function PriorityBadge({ priority }) {
  const map = {
    High: "badge-danger",
    Medium: "badge-info",
    Low: "badge-accent",
  };
  return <span className={`badge ${map[priority]}`}>{priority}</span>;
}

export default function UserTable({ users }) {
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState("id");
  const [sortDir, setSortDir] = useState("asc");
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    let list = users.filter(
      (u) =>
        u.name.toLowerCase().includes(query.toLowerCase()) ||
        u.device.toLowerCase().includes(query.toLowerCase()) ||
        u.ip.includes(query) ||
        u.priority.toLowerCase().includes(query.toLowerCase())
    );
    list = [...list].sort((a, b) => {
      let va = a[sortKey];
      let vb = b[sortKey];
      if (typeof va === "string") {
        va = va.toLowerCase();
        vb = vb.toLowerCase();
      }
      if (va < vb) return sortDir === "asc" ? -1 : 1;
      if (va > vb) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
    return list;
  }, [users, query, sortKey, sortDir]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const pageRows = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);

  const toggleSort = (key) => {
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const SortTh = ({ k, children }) => (
    <th onClick={() => toggleSort(k)} className={`sortable ${sortKey === k ? `sorted-${sortDir}` : ""}`}>
      {children} <span className="sort-arrow">{sortKey === k ? (sortDir === "asc" ? "▲" : "▼") : "⇅"}</span>
    </th>
  );

  return (
    <div className="user-table glass">
      <div className="table-head">
        <h3 className="section-title"><span className="dot" /> Connected Users</h3>
        <div className="table-search">
          <FiSearch />
          <input
            type="text"
            placeholder="Search user / device / IP…"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPage(1);
            }}
          />
        </div>
      </div>

      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <SortTh k="username">User</SortTh>
              <SortTh k="device">Device</SortTh>
              <SortTh k="priority">Priority</SortTh>
              <SortTh k="usage">Usage</SortTh>
              <SortTh k="allocated">Allocated</SortTh>
              <SortTh k="status">Status</SortTh>
            </tr>
          </thead>
          <tbody>
            <AnimatePresence mode="popLayout">
              {pageRows.map((u, i) => (
                <motion.tr
                  key={u.id}
                  layout
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ delay: i * 0.04, duration: 0.3 }}
                >
                  <td>
                    <div className="cell-user">
                      <span className="user-avatar">{u.name.charAt(0)}</span>
                      <div>
                        <p className="cell-name">{u.name}</p>
                        <p className="cell-sub mono">{u.ip}</p>
                      </div>
                    </div>
                  </td>
                  <td>{u.deviceIcon} {u.device}</td>
                  <td><PriorityBadge priority={u.priority} /></td>
                  <td>
                    <div className="usage-cell">
                      <strong>{u.usage} Mbps</strong>
                      <div className="progress-track mini">
                        <div
                          className="progress-fill"
                          style={{ width: `${Math.round((u.usage / u.allocated) * 100)}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="mono">{u.allocated} Mbps</td>
                  <td><StatusBadge status={u.status} /></td>
                </motion.tr>
              ))}
            </AnimatePresence>
            {pageRows.length === 0 && (
              <tr>
                <td colSpan="6" className="empty-row">No users match your search 🔍</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="pagination">
        <button
          className="page-btn"
          disabled={safePage <= 1}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
        >
          <FiChevronLeft /> Prev
        </button>
        <div className="page-nums">
          {Array.from({ length: totalPages }, (_, i) => (
            <button
              key={i}
              className={`page-num ${safePage === i + 1 ? "active" : ""}`}
              onClick={() => setPage(i + 1)}
            >
              {i + 1}
            </button>
          ))}
        </div>
        <button
          className="page-btn"
          disabled={safePage >= totalPages}
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
        >
          Next <FiChevronRight />
        </button>
      </div>
    </div>
  );
}