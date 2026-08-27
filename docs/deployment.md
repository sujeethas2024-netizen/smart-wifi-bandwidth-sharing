# Deployment Guide — Public Access (Any WiFi / Mobile Data)

## 1. Local LAN mode (default)

This is the current default behavior:

```bash
python -m backend.app
```

- Access on host PC: `http://localhost:5000`
- Access on same WiFi: `http://<PC-IP>:5000`
- Access via QR code: `qr_code.png`

## 2. Public Internet mode (any WiFi / mobile data)

To make the app accessible from **any network** (home, office, mobile data, different country), deploy it to a public host.

### Option A: Render.com (recommended for research paper)

1. Push this repo to GitHub.
2. Go to [Render Dashboard → New → Blueprint](https://dashboard.render.com/blueprints).
3. Connect your GitHub repo and click **Apply**.
4. Render uses `render.yaml` automatically:
   - Builds the Python backend
   - Starts `python -m backend.app`
   - Gives you a public URL like `https://smart-wifi-bandwidth-sharing.onrender.com`
5. **Important:** set the environment variable `PUBLIC_API_BASE` to `/` in Render's dashboard if the frontend and backend are on different subpaths.

After deployment, **any user on any WiFi or mobile data** can open that public URL in a browser, register, and use the dashboard.

### Option B: VPS / Cloud VM (AWS / GCP / Azure / Oracle / DigitalOcean)

1. Copy the project to a Linux VM.
2. Install dependencies:
   ```bash
   sudo apt update && sudo apt install -y python3-venv nodejs npm
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cd frontend && npm install && npm run build && cd ..
   ```
3. Run with a production server:
   ```bash
   python -m backend.app
   ```
4. Use **nginx** or **Caddy** as a reverse proxy on ports 80/443 with a domain name.
5. Users access `https://your-domain.com` from any network.

### Option C: Tunneling (temporary demo)

If you want to demo from your local PC without cloud hosting:

- **ngrok**: `ngrok http 5000`
- **Cloudflare Tunnel**: `cloudflared tunnel --url http://localhost:5000`

This creates a public URL that tunnels to your local server. Keep the local PC running.

## 3. Frontend configuration for split deployments

If you serve the React frontend separately from Flask (e.g., Vercel + Render API):

```bash
# In frontend/.env.production
VITE_API_BASE=https://your-api-domain.com
```

Or set a runtime global in the HTML `<head>`:

```html
<script>window.__API_BASE__="https://your-api-domain.com"</script>
```

The app reads `apiBase()` in this order:
1. `import.meta.env.VITE_API_BASE`
2. `window.__API_BASE__`
3. `""` (same-origin)

## 4. Multi-user access

Once publicly hosted:
- Any number of users can open the URL simultaneously.
- The Flask backend maintains **one shared in-memory network state** (`_state` in `backend/routes/network_routes.py`) so all users see the same live numbers.
- User accounts are stored in SQLite (`database/accounts.db`), so registrations persist across restarts.
