# Smart Wi-Fi Bandwidth Sharing Using Game Theory

A Game Theory based system for fair and efficient allocation of Wi-Fi bandwidth among multiple users.

## Architecture

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

- **Central Controller**: Flask + Game Theory engine (Nash Equilibrium, Jain's Fairness Index).
- **Access Points**: Any standard WiFi 5/6 router. Managed APs (Cisco Meraki, Aruba, Ubiquiti) enable deeper integration.
- **Users**: Any device with a browser — phones, laptops, tablets. No app install required.

## 🚀 Quick Start (Local / LAN)

**Double-click `START_APP.bat`** in the project folder. That's it.

The launcher automatically:
1. Builds the frontend on first run (skipped afterwards)
2. Detects your PC's WiFi IP
3. Shows **both permanent links** and opens your browser

```
On this PC ........  http://localhost:5000
On WiFi devices ...  http://<YOUR-WIFI-IP>:5000   ← phones/laptops on same WiFi
```

These links are **permanent** — bookmark them once, reuse forever.
The server also auto-restarts if it ever stops.

> 💡 Run `CREATE_DESKTOP_SHORTCUT.bat` **once** to get a "Smart WiFi App"
> icon on your Desktop — then launch with a single double-click forever.

### 📱 Opening the site on your phone

A scannable **QR code** appears in the launcher window every time the server
starts (also saved as `qr_code.png`) — point your phone camera at it.

**If the phone cannot connect, check these in order:**
1. **Phone must be on the SAME WiFi as this PC** — turn OFF mobile data
   (5G/LTE) on the phone, then reload the page.
2. **College/office WiFi blocking devices?** Many shared WiFi networks
   isolate devices from each other. The fix that always works:
   - Turn ON **Mobile Hotspot** on your phone
   - Connect this PC's WiFi to the phone's hotspot
   - Restart `START_APP.bat` — it detects the new IP automatically
   - Open the new link on the phone (the phone IS the network, so it
     always works)
3. **Firewall**: already handled automatically — the launcher adds the
   required rule once (Windows asks permission the first time).

## 🌍 Public Access (Any WiFi / Mobile Data)

To let users access the dashboard from **any network** (home, office, mobile data, different country), deploy it to a public host.

### Option A: Render.com (recommended)

1. Push this repo to GitHub.
2. Go to [Render Dashboard → New → Blueprint](https://dashboard.render.com/blueprints).
3. Connect your GitHub repo and click **Apply**.
4. Render uses `render.yaml` automatically and gives you a public URL like:
   `https://smart-wifi-bandwidth-sharing.onrender.com`
5. Set environment variable `PUBLIC_API_BASE` to `/` in Render dashboard if needed.

### Option B: VPS / Cloud (AWS / GCP / Azure / DigitalOcean)

```bash
# Linux VM
sudo apt update && sudo apt install -y python3-venv nodejs npm
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
python -m backend.app
```

Use **nginx** or **Caddy** as a reverse proxy on ports 80/443 with a domain name.

### Option C: Tunneling (temporary demo)

```bash
# ngrok
ngrok http 5000

# Cloudflare Tunnel
cloudflared tunnel --url http://localhost:5000
```

## 🧮 Game Theory Concepts

- Non-Cooperative Game Theory
- Congestion Game
- Utility Functions
- Best Response
- Nash Equilibrium
- Jain's Fairness Index

## 🛠️ Technologies

- Python / Flask
- SQLite (accounts) + MySQL (allocation history)
- React + Vite + Chart.js
- Game Theory engine (NumPy / SciPy)

## 📂 Project Structure

```
backend/
  app.py                  # Flask entry point
  routes/                 # API endpoints
  services/               # Allocation engine
  game_theory/            # Nash equilibrium + utility
  database/               # SQLite + MySQL
frontend/
  src/
    pages/                # Admin / User dashboards
    components/           # Charts, tables, topology
    hooks/                # useLiveUsers, useNetworkStats
    services/             # API client
docs/
  game_theory.md          # Theory reference
  wifi-architecture.md    # System design for paper
  deployment.md           # Public hosting guide
```

## 👥 Team

- Sujeetha
- Bindu