"""
main.py

FastAPI backend for the Smart Energy Monitoring Dashboard.

Data source: MongoDB (see app/db.py) instead of the old Excel prototype.
Weather:     OpenWeatherMap, fetched on demand and cached per node
             (see app/weather_service.py).
Relay control: hardware-first via app/hardware_client.py, then MongoDB
             (see app/relay_controller.py).

Run locally:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Deployed on Vercel via backend/api/index.py, which just imports `app` from
here - see that file and the root vercel.json.
"""

import os

from dotenv import load_dotenv

load_dotenv()  # loads backend/.env if present (local dev only; no-op on Vercel)

from fastapi import FastAPI, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware

from app import db
from app import weather_service
from app.relay_controller import set_relay as controller_set_relay
from app.schemas import (
    DashboardSummary,
    DeleteResponse,
    NodeCreate,
    NodeDetail,
    NodeSummary,
    NodeUpdate,
    RelayControlRequest,
    RelayControlResponse,
    WeatherInfo,
    WeatherRefreshResponse,
)

app = FastAPI(
    title="Smart Energy Monitoring Dashboard API",
    description="Backend for the Parent/Gateway Node dashboard (MongoDB-backed).",
    version="2.0.0",
)

FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN] if FRONTEND_ORIGIN != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SORTABLE_FIELDS = {"power", "energy_consumption", "voltage", "current", "node_id", "status"}

# ---------------------------------------------------------------------------
# Optional simple write-protection. If DASHBOARD_API_KEY is set, every
# mutating request (create/update/delete/relay/weather-refresh) must send
# header  Authorization: Bearer <DASHBOARD_API_KEY>.
# Left unset by default so local/dev usage stays simple.
# ---------------------------------------------------------------------------
DASHBOARD_API_KEY = os.environ.get("DASHBOARD_API_KEY", "")


def require_api_key(authorization: str | None = Header(default=None)):
    if not DASHBOARD_API_KEY:
        return  # protection disabled
    expected = f"Bearer {DASHBOARD_API_KEY}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header.")


def _to_summary(row: dict) -> NodeSummary:
    return NodeSummary(
        node_id=row["node_id"],
        node_name=row["node_name"],
        location=row["location"],
        voltage=row["voltage"],
        current=row["current"],
        power=row["power"],
        energy_consumption=row["energy_consumption"],
        power_factor=row["power_factor"],
        status=row["status"],
        relay_state=row["relay_state"],
        last_seen=row["last_seen"],
    )


def _to_detail(row: dict) -> NodeDetail:
    return NodeDetail(
        **_to_summary(row).model_dump(),
        latitude=row["latitude"],
        longitude=row["longitude"],
        parent_gateway=row["parent_gateway"],
        frequency=row["frequency"],
        weather=WeatherInfo(**row["weather"]),
    )


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary():
    rows = db.read_all_nodes()

    online = [r for r in rows if r["status"] == "Online"]
    offline = [r for r in rows if r["status"] != "Online"]
    total_power = round(sum(r["power"] for r in rows), 1)
    total_energy = round(sum(r["energy_consumption"] for r in rows), 2)

    highest = max(rows, key=lambda r: r["power"], default=None)
    lowest = min(rows, key=lambda r: r["power"], default=None)

    return DashboardSummary(
        total_nodes=len(rows),
        online_nodes=len(online),
        offline_nodes=len(offline),
        total_power=total_power,
        total_energy=total_energy,
        highest_consuming=_to_summary(highest) if highest else None,
        lowest_consuming=_to_summary(lowest) if lowest else None,
        last_refreshed=db.get_last_refreshed(),
    )


@app.get("/api/nodes", response_model=list[NodeSummary])
def list_nodes(
    search: str | None = Query(None, description="Search by Node ID, Name, or Location"),
    sort_by: str | None = Query(None, description="power | energy_consumption | voltage | current | node_id | status"),
    order: str = Query("desc", description="asc | desc"),
    filter: str = Query("all", description="all | online | offline | highest | lowest"),
):
    rows = db.read_all_nodes()

    if search:
        q = search.strip().lower()
        rows = [
            r for r in rows
            if q in r["node_id"].lower()
            or q in r["node_name"].lower()
            or q in r["location"].lower()
        ]

    filter = (filter or "all").lower()
    if filter == "online":
        rows = [r for r in rows if r["status"] == "Online"]
    elif filter == "offline":
        rows = [r for r in rows if r["status"] != "Online"]
    elif filter == "highest":
        rows = sorted(rows, key=lambda r: r["power"], reverse=True)[:5]
    elif filter == "lowest":
        rows = sorted(rows, key=lambda r: r["power"])[:5]

    if sort_by:
        sort_by = sort_by.lower()
        if sort_by not in SORTABLE_FIELDS:
            raise HTTPException(status_code=400, detail=f"sort_by must be one of {sorted(SORTABLE_FIELDS)}")
        reverse = order.lower() != "asc"
        rows = sorted(rows, key=lambda r: r[sort_by], reverse=reverse)

    return [_to_summary(r) for r in rows]


@app.get("/api/nodes/{node_id}", response_model=NodeDetail)
def node_detail(node_id: str):
    row = db.get_node(node_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")
    return _to_detail(row)


# ---------------------------------------------------------------------------
# Node management: Add / Edit / Remove
# ---------------------------------------------------------------------------
@app.post("/api/nodes", response_model=NodeDetail, status_code=201)
def create_node(payload: NodeCreate, authorization: str | None = Header(default=None)):
    require_api_key(authorization)
    try:
        row = db.create_node(payload.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return _to_detail(row)


@app.patch("/api/nodes/{node_id}", response_model=NodeDetail)
def edit_node(node_id: str, payload: NodeUpdate, authorization: str | None = Header(default=None)):
    require_api_key(authorization)
    updates = payload.model_dump(exclude_none=True)
    row = db.update_node(node_id, updates)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")
    return _to_detail(row)


@app.delete("/api/nodes/{node_id}", response_model=DeleteResponse)
def remove_node(node_id: str, authorization: str | None = Header(default=None)):
    require_api_key(authorization)
    deleted = db.delete_node(node_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")
    return DeleteResponse(node_id=node_id, deleted=True, message=f"Node '{node_id}' removed.")


# ---------------------------------------------------------------------------
# Relay control (hardware-first, then DB - see relay_controller.py)
# ---------------------------------------------------------------------------
@app.post("/api/nodes/{node_id}/relay", response_model=RelayControlResponse)
def set_relay(node_id: str, req: RelayControlRequest, authorization: str | None = Header(default=None)):
    require_api_key(authorization)
    state = req.state.strip().upper()
    if state not in ("ON", "OFF"):
        raise HTTPException(status_code=400, detail="state must be 'ON' or 'OFF'")

    success, message, _updated = controller_set_relay(node_id, state)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return RelayControlResponse(node_id=node_id, relay_state=state, success=success, message=message)


# ---------------------------------------------------------------------------
# Weather: fetch fresh data for one node, on demand
# ---------------------------------------------------------------------------
@app.post("/api/nodes/{node_id}/weather/refresh", response_model=WeatherRefreshResponse)
def refresh_weather(node_id: str, authorization: str | None = Header(default=None)):
    require_api_key(authorization)
    row = db.get_node(node_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")

    try:
        fresh = weather_service.fetch_live_weather(row["latitude"], row["longitude"])
    except weather_service.WeatherFetchError as e:
        raise HTTPException(status_code=502, detail=str(e))

    updated = db.set_weather(node_id, fresh)
    return WeatherRefreshResponse(
        node_id=node_id,
        weather=WeatherInfo(**updated["weather"]),
        message="Weather updated from OpenWeatherMap.",
    )
