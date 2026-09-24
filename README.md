# Smart Energy Monitoring System — Gateway Dashboard (v2)

A dashboard for the **Parent/Gateway Node** in a LoRa-based energy monitoring
network. This version replaces the original Excel prototype with **MongoDB**,
adds **live weather** (OpenWeatherMap, fetched on demand per node), full
**node management** (Add / Edit / Remove), and **hardware-aware relay
control** — the ON/OFF button now talks to a real gateway first and only
updates the database once the hardware acknowledges.

```
Child Energy Nodes → LoRa → Parent/Gateway → Python Backend → Dashboard
                                                    ↑
                                          MongoDB (nodes collection)
                                                    ↑
                                    OpenWeatherMap (per-node, on demand)
```

---

## 1. What changed from the Excel version

| Area | Before | Now |
|---|---|---|
| Data store | `energy_data.xlsx` | MongoDB (`nodes` collection) |
| Weather | Static columns in Excel | Live pull from OpenWeatherMap, per node, on demand, cached in Mongo |
| Node management | Edit the Excel file by hand | Add / Edit / Remove nodes from the dashboard UI, backed by REST endpoints |
| Relay control | Writes straight to Excel | Calls the hardware layer first (`hardware_client.py`); DB only updates after a hardware ack |
| Deployment | Local Raspberry Pi only | Deployable as two simple Vercel projects (or still runnable locally / on a Pi) |

The project structure and swappable-layer philosophy stay the same — you can
keep tracing `main.py → relay_controller.py / weather_service.py → db.py`
the same way you did with the Excel version.

---

## 2. Project structure

```
smart-energy-dashboard/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + all REST routes
│   │   ├── db.py                # MongoDB data layer (THE data source now)
│   │   ├── relay_controller.py  # Hardware-first relay orchestration
│   │   ├── hardware_client.py   # Talks to your real Gateway (or simulates)
│   │   ├── weather_service.py   # OpenWeatherMap client
│   │   └── schemas.py           # Pydantic models incl. Create/Update
│   ├── api/
│   │   └── index.py             # Vercel serverless entrypoint
│   ├── seed_mongo.py            # Populates MongoDB with 18 sample nodes
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── TopBar.jsx            # + "Add Node" button
│   │   │   ├── SummaryPanel.jsx
│   │   │   ├── Toolbar.jsx
│   │   │   ├── NodeTable.jsx
│   │   │   ├── NodeDetailDrawer.jsx  # + Edit / Delete / Refresh weather
│   │   │   ├── NodeFormModal.jsx     # Add / Edit node form
│   │   │   └── Badges.jsx
│   │   ├── api.js                # Configurable API base URL + all endpoints
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
└── README.md
```

---

## 3. MongoDB — what's stored, and why it's flexible

Database: whatever you name it (`MONGODB_DB_NAME`, default `energy_monitoring`).
Collection: `nodes`. One document per node, unique on `node_id`.

Fields the dashboard actively uses:

```
node_id, node_name, location, latitude, longitude, parent_gateway,
voltage, current, power, energy_consumption, power_factor, frequency,
status, last_seen, relay_state,
weather: { temperature, humidity, rain, wind_speed, weather_condition, updated_at }
```

**You said your Mongo documents might carry more fields than the dashboard
needs, or a new node might be missing some fields at first — both are
handled on purpose:**

- `app/db.py`'s `normalize_node()` fills in a sensible default for any
  missing field (0 for numbers, `"Offline"`/`"OFF"` for status/relay, empty
  string for text) so a half-filled document never breaks the API.
- Any *extra* fields your Mongo documents have (say, a firmware version, a
  battery level, an install date) are simply ignored by the API — they stay
  in the database untouched, ready for you to expose later by adding one
  field to `schemas.py`, `db.py`'s `DEFAULTS`, and the relevant React
  component. Nothing about the current schema is "locked in."

### Seeding sample data

```bash
cd backend
export MONGODB_URI="mongodb+srv://<user>:<pass>@<cluster>.mongodb.net"
python seed_mongo.py            # inserts/updates the 18 sample nodes
python seed_mongo.py --wipe     # wipes the collection first
```

This also creates the required unique index on `node_id` — run it at least
once against any new database, even if you don't want the sample nodes (you
can delete them from the dashboard afterward).

---

## 4. Live weather (OpenWeatherMap)

- Get a free API key: https://openweathermap.org/api
- Set `OPENWEATHER_API_KEY` in the backend environment.
- Weather is **not** fetched automatically for every node on every page
  load (that would burn through API quota fast). Instead, each node's
  detail panel has a **Refresh** button next to "Weather at Node Location"
  that calls:

  ```
  POST /api/nodes/{node_id}/weather/refresh
  ```

  This pulls current temperature, humidity, rain, wind speed, and condition
  for that node's exact `latitude`/`longitude`, and stores it back onto the
  node's own MongoDB document (with an `updated_at` timestamp), so the next
  page load shows the cached value instantly without calling the API again.
- A brand-new node shows "Not fetched yet" until you click Refresh once.

If you'd rather auto-refresh weather for all nodes on a schedule instead of
per-node buttons, add a small cron-triggered endpoint or a scheduled Vercel
Cron Job that loops `db.read_all_nodes()` and calls
`weather_service.fetch_live_weather()` for each — the pieces are already
there, this is just a matter of wiring a loop and a schedule.

---

## 5. Node management — Add / Edit / Remove

- **Add Node** button (top bar) opens a form: Node ID, Name, Location,
  Latitude, Longitude, Parent Gateway, Status. Electrical readings are
  intentionally left out of this form — those come from the sensor/gateway
  once the node is actually reporting, not typed by hand.
- **Edit** (pencil icon in the node detail drawer) lets you update the same
  metadata fields for an existing node.
- **Remove** (trash icon) deletes the node from MongoDB after a confirmation
  dialog.

REST endpoints, if you want to script this instead:

```
POST   /api/nodes                body: NodeCreate
PATCH  /api/nodes/{node_id}      body: NodeUpdate (any subset of fields)
DELETE /api/nodes/{node_id}
```

---

## 6. ON/OFF control — now hardware-aware

`relay_controller.py`'s `set_relay()` now does this, in order:

1. Look up the node; refuse if it's Offline (nothing to command).
2. Call `hardware_client.send_relay_command(node_id, state)`.
3. **Only if that call succeeds**, write the new `relay_state` into MongoDB.

This means the database can never claim a state the physical node didn't
actually reach — if the hardware call fails, the dashboard shows the error
and the old (true) state stays put.

### Today (no hardware yet)

`HARDWARE_MODE=none` (the default). `hardware_client.py` logs the command
and returns success immediately, so the whole dashboard — including Mongo
updates — works end-to-end while you build the physical side.

### Later (real Gateway/LoRa)

Your Gateway (the Raspberry Pi with the LoRa radio) runs its own small
listener — any tiny HTTP server (Flask, FastAPI, even a few lines of
`http.server`) that:

```
POST /relay
{ "node_id": "N-01", "state": "ON" }
```

...and translates that into an actual LoRa packet to the child node using
whatever radio driver you're using (RFM95/SX127x via SPI, a vendor SDK,
etc.), then responds `200 OK` once the child node acknowledges.

On the dashboard backend side, set:

```
HARDWARE_MODE=webhook
GATEWAY_WEBHOOK_URL=https://your-gateway-address/relay
GATEWAY_API_KEY=some-shared-secret        # optional but recommended
```

Nothing else changes — same route, same request/response shape, same React
button. If your cloud backend can't reach the Pi directly (it's behind a
home router with no public IP), expose the Pi's listener through a tunnel
(Cloudflare Tunnel, Tailscale Funnel, or ngrok) and point
`GATEWAY_WEBHOOK_URL` at that public tunnel address instead.

---

## 7. Environment variables — full list

**Backend** (`backend/.env` locally, or Vercel Project → Environment Variables):

| Variable | Default | Purpose |
|---|---|---|
| `MONGODB_URI` | — (required) | MongoDB Atlas connection string |
| `MONGODB_DB_NAME` | `energy_monitoring` | Database name |
| `OPENWEATHER_API_KEY` | — | Required for the weather Refresh button |
| `HARDWARE_MODE` | `none` | `none` (simulated) or `webhook` (real gateway) |
| `GATEWAY_WEBHOOK_URL` | — | Your gateway's relay endpoint, when `HARDWARE_MODE=webhook` |
| `GATEWAY_API_KEY` | — | Sent as `Authorization: Bearer <key>` to the gateway |
| `GATEWAY_TIMEOUT_SECONDS` | `6` | HTTP timeout for the gateway call |
| `DASHBOARD_API_KEY` | — | If set, all writes require `Authorization: Bearer <key>` |
| `FRONTEND_ORIGIN` | `*` | Lock CORS to your deployed frontend's URL in production |

**Frontend** (`frontend/.env` locally, or Vercel Project → Environment Variables):

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `/api` (via dev proxy) | Your backend's full URL + `/api` in production |
| `VITE_DASHBOARD_API_KEY` | — | Only needed if you set `DASHBOARD_API_KEY` on the backend |

Copy `.env.example` → `.env` in each folder to get started locally.

---

## 8. Running locally

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env            # then fill in MONGODB_URI at least
python seed_mongo.py            # first time only, or to reset sample data
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend** (second terminal):
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. `VITE_API_BASE_URL` can stay empty locally —
Vite's dev proxy forwards `/api/*` to `http://127.0.0.1:8000` automatically
(see `vite.config.js`).

---

## 9. Deploying to Vercel (simple: two zero-config projects)

You don't need a `vercel.json` for either side — Vercel auto-detects both.
From the same GitHub repo, create **two** Vercel projects:

### Project A — Backend
1. Import the repo, set **Root Directory** to `backend`.
2. Vercel auto-detects the Python function at `backend/api/index.py`
   (it re-exports the FastAPI `app`) and deploys it as a serverless
   function — no config file needed.
3. Add the backend environment variables from the table above (at minimum
   `MONGODB_URI`).
4. Deploy. Note the resulting URL, e.g. `https://energy-backend.vercel.app`.
5. In **MongoDB Atlas → Network Access**, allow access from anywhere
   (`0.0.0.0/0`) — Vercel serverless functions use dynamic IPs, so a fixed
   IP allow-list won't work on the free tier.
6. Run `python seed_mongo.py` once, pointed at the same `MONGODB_URI`, from
   your laptop (or any machine) to seed/reset sample data — this doesn't
   need to run on Vercel itself.

### Project B — Frontend
1. Import the same repo again as a second project, set **Root Directory**
   to `frontend`. Vercel auto-detects Vite.
2. Add environment variable:
   ```
   VITE_API_BASE_URL = https://energy-backend.vercel.app/api
   ```
   (use the URL from Project A, step 4)
3. Deploy. That's your dashboard's public URL.
4. Optional: go back to Project A and set `FRONTEND_ORIGIN` to this
   frontend URL exactly, to lock down CORS instead of leaving it at `*`.

That's the whole deployment — two "Import Project" clicks, a handful of
environment variables, no build scripts or config files to hand-write.

### Notes / limits worth knowing
- Vercel's free tier serverless functions have a request timeout (10s on
  Hobby, longer on Pro). Our endpoints are simple CRUD + one external API
  call, well within that, but a slow `GATEWAY_WEBHOOK_URL` could push
  close to it — keep `GATEWAY_TIMEOUT_SECONDS` reasonably short.
- Cold starts: the very first request after idle time will be slightly
  slower (MongoDB reconnects). Subsequent requests reuse the cached
  connection (see `db.py`).
- If you'd rather run the backend somewhere with a persistent process
  instead (Railway, Render, Fly.io, or your Raspberry Pi itself), that
  works exactly the same way — just point `VITE_API_BASE_URL` at wherever
  it lives. Nothing about the backend code is Vercel-specific.

---

## 10. Dashboard features (unchanged, still no charts/graphs)

Summary strip, search (Node ID / Name / Location), sort (Power / Energy /
Voltage / Current / Node ID / Status, both directions), quick filters
(All / Online / Offline / Highest / Lowest Consumption), node table, and
the node detail drawer (Electrical, Node Info, Weather, ON/OFF control) —
all exactly as before, now backed by MongoDB and live weather, plus:

- **Add Node** button in the top bar
- **Edit** and **Delete** icons in the detail drawer header
- **Refresh** button next to the Weather section

---

## 11. Known limitations / good next steps

- No historical/time-series storage yet — `energy_consumption` is a
  snapshot value per node, not a logged series over time. A natural next
  step is a second Mongo collection (`readings`) that the gateway appends
  to periodically, with the dashboard's "Energy" figure becoming a
  computed sum/range query instead of a stored field.
- No authentication on the dashboard UI itself (only an optional API key
  for write endpoints). Fine for a college demo; add real auth before
  using this anywhere semi-public.
- `HARDWARE_MODE=webhook` assumes your gateway is reachable over HTTP from
  the internet (directly or via a tunnel). If you later move to MQTT
  instead (common for LoRa gateways), replace the body of
  `hardware_client._send_via_webhook` with an MQTT publish call — the
  function signature and everything calling it stays the same.
- CORS defaults to `*` for ease of setup; tighten `FRONTEND_ORIGIN` once
  your frontend URL is stable.
