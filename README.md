# Smart Wi-Fi Bandwidth Sharing Using Game Theory

A Game Theory based system for fair and efficient allocation of Wi-Fi bandwidth among multiple users.

## 🚀 Quick Start (Permanent Links — No Setup Needed Again)

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

### Manual start (alternative)
```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
.venv\Scripts\python -m backend.app
```

## Project Objective

The system models Wi-Fi users as players competing for a limited bandwidth resource.

## Game Theory Concepts

- Non-Cooperative Game Theory
- Congestion Game
- Utility Functions
- Best Response
- Nash Equilibrium
- Jain's Fairness Index

## Technologies

- Python
- Flask
- MySQL
- HTML
- CSS
- Bootstrap
- JavaScript
- Chart.js

## Project Flow

User
→ Bandwidth Request
→ Game Theory Engine
→ Nash Equilibrium
→ Bandwidth Allocation
→ Dashboard

## Team

- Sujeetha
- Bindu