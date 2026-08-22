/* ============================================================
   Mock network data — simulates a live WiFi network.
   In production these functions can be swapped for the Flask
   backend endpoints (see services/api.js).
   ============================================================ */

const DEVICE_TYPES = [
  { type: "Laptop", icon: "💻" },
  { type: "Mobile", icon: "📱" },
  { type: "TV", icon: "📺" },
  { type: "Tablet", icon: "📲" },
  { type: "Desktop", icon: "🖥️" },
  { type: "Smart Speaker", icon: "🔊" },
  { type: "Gaming Console", icon: "🎮" },
  { type: "IoT Camera", icon: "📷" },
];

const PRIORITIES = ["High", "Medium", "Low"];
const STATUSES = ["online", "online", "online", "idle", "offline"];
const SIGNALS = ["excellent", "excellent", "good", "good", "fair", "weak"];
const ROOMS = ["Living Room", "Bedroom", "Kitchen", "Hall", "Study Room"];

const FIRST = [
  "Aarav", "Diya", "Rohan", "Sneha", "Kiran", "Meera", "Arjun", "Priya",
  "Vikram", "Ananya", "Farhan", "Kavya", "Nikhil", "Ishita", "Sameer",
  "Tanvi", "Yash", "Neha", "Aditya", "Pooja", "Manav", "Riya", "Dev", "Zara",
];
const LAST = ["Sharma", "Patel", "Reddy", "Iyer", "Khan", "Verma", "Nair", "Gupta"];

const rand = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;
const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];

function makeUsers(count = 24) {
  const users = [];
  for (let i = 0; i < count; i++) {
    const device = pick(DEVICE_TYPES);
    const priority = PRIORITIES[i % 3 === 0 ? rand(0, 2) : rand(0, 2)];
    const status = i < count - 3 ? pick(STATUSES.slice(0, 4)) : "offline";
    const signal = status === "offline" ? "weak" : pick(SIGNALS);
    const allocated =
      priority === "High" ? rand(18, 30) : priority === "Medium" ? rand(10, 17) : rand(4, 9);

    users.push({
      id: i + 1,
      name: `${FIRST[i % FIRST.length]} ${pick(LAST)}`,
      username: `user${i + 1}`,
      device: device.type,
      deviceIcon: device.icon,
      ip: `192.168.0.${10 + i}`,
      mac: `A4:${rand(10, 99)}:${rand(10, 99)}:${rand(10, 99)}:${rand(10, 99)}:${rand(10, 99)}`,
      priority,
      usage: Math.min(allocated, rand(2, allocated)),
      allocated,
      status,
      signal,
      room: pick(ROOMS),
      connectedSince: `${rand(1, 12)}h ${rand(0, 59)}m`,
      dataUsed: (rand(120, 4200) / 100).toFixed(1),
    });
  }
  return users;
}

export function generateUsers() {
  return makeUsers();
}

export function generateStats(users) {
  const online = users.filter((u) => u.status === "online");
  const activeDevices = new Set(online.map((u) => u.device)).size;
  const bandwidth = online.reduce((s, u) => s + u.usage, 0);
  const health = Math.max(
    62,
    Math.min(99, 100 - Math.round(bandwidth / 6) + rand(-2, 3))
  );
  return {
    connectedUsers: online.length,
    totalUsers: users.length,
    activeDevices,
    bandwidth,
    health,
    healthLabel:
      health >= 90 ? "Excellent" : health >= 75 ? "Good" : health >= 65 ? "Fair" : "Poor",
  };
}

export function generateHistory(points = 20) {
  const labels = [];
  const values = [];
  let v = 60;
  for (let i = points - 1; i >= 0; i--) {
    labels.push(`-${i * 5}s`);
    v = Math.max(35, Math.min(98, v + rand(-8, 8)));
    values.push(v);
  }
  return { labels, values };
}

export function generateCategoryData() {
  return {
    labels: ["Streaming", "Gaming", "Browsing", "Downloads", "Video Calls"],
    datasets: [
      {
        label: "Consumption (Mbps)",
        data: [rand(15, 28), rand(8, 16), rand(6, 14), rand(10, 22), rand(5, 12)],
        backgroundColor: [
          "#2563eb",
          "#7c3aed",
          "#14b8a6",
          "#f59e0b",
          "#ef4444",
        ],
        borderRadius: 8,
      },
    ],
  };
}

export function generateAllocationPie(users) {
  const top = [...users]
    .filter((u) => u.status !== "offline")
    .sort((a, b) => b.allocated - a.allocated)
    .slice(0, 5);
  const rest = users
    .filter((u) => u.status !== "offline")
    .slice(5)
    .reduce((s, u) => s + u.allocated, 0);

  return {
    labels: [...top.map((u) => u.username), "Others"],
    datasets: [
      {
        data: [...top.map((u) => u.allocated), rest],
        backgroundColor: ["#2563eb", "#7c3aed", "#14b8a6", "#f59e0b", "#ef4444", "#64748b"],
        borderColor: "transparent",
        hoverOffset: 10,
      },
    ],
  };
}

export const NOTIFICATIONS = [
  { id: 1, icon: "📱", title: "New device connected", body: "Galaxy S24 joined the network (192.168.0.31)", time: "Just now", tone: "info" },
  { id: 2, icon: "⚖️", title: "Bandwidth reallocated", body: "Game theory equilibrium recomputed for 18 devices", time: "2 min ago", tone: "accent" },
  { id: 3, icon: "🔄", title: "Router restarted", body: "Firmware update completed successfully", time: "26 min ago", tone: "success" },
  { id: 4, icon: "⚠️", title: "High load detected", body: "Living Room AP at 92% capacity", time: "1 hr ago", tone: "warning" },
];

export const RECOMMENDATIONS = [
  { id: 1, text: "Allocate more bandwidth to User 3 — heavy video conferencing detected", tone: "info", action: true },
  { id: 2, text: "Device 5 (IoT Camera) inactive for 48h — consider throttling to 1 Mbps", tone: "warning", action: true },
  { id: 3, text: "Fairness Index Excellent (0.94) — Jain index above threshold", tone: "success", action: false },
  { id: 4, text: "Shift 5 Mbps from idle devices to peak-hour streaming pool", tone: "info", action: true },
  { id: 5, text: "Enable QoS prioritization for gaming console during 8–11 PM", tone: "accent", action: true },
];

export const COVERAGE_ROOMS = [
  { name: "Living Room", icon: "🛋️", strength: 96, devices: 6 },
  { name: "Bedroom", icon: "🛏️", strength: 82, devices: 4 },
  { name: "Kitchen", icon: "🍳", strength: 64, devices: 2 },
  { name: "Hall", icon: "🚪", strength: 88, devices: 3 },
  { name: "Study Room", icon: "📚", strength: 74, devices: 3 },
];

export const PERFORMANCE = () => ({
  latency: rand(8, 22),
  packetLoss: +(Math.random() * 1.2).toFixed(2),
  throughput: rand(88, 99),
  jitter: rand(1, 6),
});

/* Simulate one tick of live traffic on all users */
export function tickUsers(users) {
  return users.map((u) => {
    if (u.status === "offline") return u;
    let usage = u.usage + rand(-3, 3);
    usage = Math.max(1, Math.min(u.allocated, usage));
    // Occasionally flip an idle device back online / vice versa
    let status = u.status;
    if (status === "idle" && Math.random() < 0.08) status = "online";
    if (status === "online" && Math.random() < 0.04) status = "idle";
    return { ...u, usage, status };
  });
}