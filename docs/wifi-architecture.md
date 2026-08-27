# WiFi System Architecture for Research Paper

## 1. System Overview

The proposed system implements a **Centralized Bandwidth Controller (CBC)** that sits between WiFi users and the internet, allocating limited bandwidth fairly using game theory (Nash Equilibrium).

```
                    +-----------------------------+
                    |     Internet / ISP           |
                    +-------------+---------------+
                                  |
                          [ Router / Gateway ]
                                  |
                    +-------------+---------------+
                    |   Central Bandwidth Controller  |
                    |   (Flask Backend + Game Theory) |
                    +-------------+---------------+
                                  |
                    +-------------+---------------+
                    |      WiFi Access Point(s)      |
                    |   (Any 802.11n/ac/ax router)   |
                    +-------------+---------------+
                                  |
            +----------+----------+----------+----------+
            |          |          |          |          |
         [Laptop]   [Mobile]   [TV]     [Tablet]   [IoT]
```

## 2. Required WiFi / Network Hardware

### Minimum viable setup (demo / lab)

| Component | Recommendation | Why |
|-----------|---------------|-----|
| **Access Point** | Any standard WiFi 5 (802.11ac) or WiFi 6 (802.11ax) router | Provides SSID, DHCP, and basic connectivity. The CBC does not require special AP firmware for the simulation mode. |
| **Central Controller Host** | Laptop, Raspberry Pi 4/5, or mini PC | Runs the Flask backend. Needs Python 3.10+ and ~1 GB RAM. |
| **Switch / Gateway** | The router itself can act as the gateway | The CBC monitors traffic via software simulation or SNMP. |
| **Client Devices** | 3–24 devices (phones, laptops, tablets) | Each logs into the web dashboard to declare usage and receive allocations. |

### Production / research-grade setup (real ISP integration)

| Component | Recommendation | Integration method |
|-----------|---------------|-------------------|
| **Managed WiFi APs** | Cisco Meraki, Aruba Instant, Ubiquiti UniFi, or OpenWRT-based APs | REST API / SNMP polling to pull per-client RSSI, airtime, and session data. |
| **Central Controller** | Dedicated Linux server or edge gateway (x86/ARM) | Runs Flask + game theory engine + optional QoS scripts. |
| **QoS Enforcement** | `tc` (Linux traffic control), `iptables`, or router QoS policies | Converts allocation decisions into rate limits / DSCP marks. |
| **Monitoring** | SNMP traps, Flow exports (NetFlow/sFlow), or proxy logs | Feeds real-time usage back into the CBC. |

### Supported WiFi standards

- **802.11n** — minimum; works for <10 users, 2.4 GHz.
- **802.11ac (WiFi 5)** — recommended; 5 GHz, MU-MIMO, better for multi-user fairness studies.
- **802.11ax (WiFi 6/6E)** — ideal for research; OFDMA and Target Wake Time enable precise per-station airtime control.

## 3. Central System Design

### Central Bandwidth Controller (CBC)

The CBC in this project is the **Flask backend** (`backend/app.py` + `backend/routes/network_routes.py`). It provides:

1. **User Management** — registration, authentication, role-based access (admin / user).
2. **Live State Server** — shared in-memory state (`_state`) with simulated bandwidth, latency, jitter, and packet loss.
3. **User Registry** — SQLite-backed account store with declared WiFi usage reasons.
4. **Game Theory Engine** — Nash equilibrium allocation (`backend/services/allocation_service.py`).
5. **REST API** — `/api/network/stats`, `/api/network/users`, `/api/allocate`, `/api/auth/*`.

### Data flow

```
User Device
    |
    | (1) HTTPS request (login / dashboard / allocation)
    |
Load Balancer / Reverse Proxy (nginx/Caddy in production)
    |
    | (2) Proxied to Flask
    |
Central Bandwidth Controller
    |
    | (3) Reads shared state + SQLite accounts
    |
    | (4) Runs congestion game / Nash solver
    |
    | (5) Returns JSON allocation + live metrics
    |
User Device
    |
    | (6) Renders dashboard with live charts
```

## 4. How It Works on Any WiFi / Mobile Data

### LAN mode (local testing)

- Server runs on `0.0.0.0:5000`.
- Phones on the **same WiFi** access `http://<host-ip>:5000`.
- The frontend calls same-origin `/api/*` endpoints.

### Public mode (any network)

When deployed to a public host (Render, VPS, etc.):

- The server listens on the host's public interface.
- The frontend is served as a static SPA by Flask (or any static host).
- Users on **any WiFi or mobile data** open the public URL.
- The API base URL resolves automatically via:
  - `VITE_API_BASE` environment variable, or
  - `window.__API_BASE__` injected by Flask, or
  - Same-origin fallback.

No VPN, no intranet, no same-WiFi restriction is needed in public mode.

## 5. Real-World Integration Path

For a real deployment where the CBC actually controls a physical router:

| Step | Action | Technology |
|------|--------|-----------|
| 1 | Discover associated clients | SNMP / RADIUS / AP vendor REST API |
| 2 | Measure real traffic | NetFlow, sFlow, or `tc` counters |
| 3 | Compute allocation | Nash Equilibrium / Proportional Fair |
| 4 | Enforce policy | QoS queues, `tc` filters, or AP admission control |
| 5 | Push updates | REST callback to router or write to RADIUS |

## 6. Notes for Research Paper

- The system is **network-agnostic**: any 802.11 AP can be used in simulation mode.
- The **centralized game theory engine** is the novel contribution; hardware integration is a standard systems engineering task.
- Fairness is measured using **Jain's Fairness Index** on the computed allocations.
- The architecture supports **n** users with polynomial-time best-response dynamics for congestion games.
