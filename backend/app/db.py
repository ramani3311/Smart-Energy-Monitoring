"""
db.py

MongoDB data access layer. This is the ONLY module that talks to MongoDB.
Every other module (main.py, relay_controller.py, weather_service.py) goes
through the functions here, so the storage backend can change again later
without touching routes or the frontend.

Connection pattern is written to be serverless-friendly (Vercel functions):
the Mongo client is created once per warm container and reused across
requests via a module-level cache, instead of reconnecting every call.

Environment variables:
    MONGODB_URI / MONGO_URI - full connection string, e.g.
                              mongodb+srv://user:pass@cluster.mongodb.net
    MONGODB_DB_NAME        - database name (default: "energy_monitoring")
"""

import os
import certifi
from datetime import datetime, timezone

from pymongo import MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError

# Checks MONGODB_URI first, falls back to MONGO_URI if set on Render/Vercel
MONGODB_URI = os.environ.get("MONGODB_URI") or os.environ.get("MONGO_URI", "")
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "energy_monitoring")
NODES_COLLECTION = "nodes"

_client_cache = {"client": None}


def get_client() -> MongoClient:
    if _client_cache["client"] is None:
        if not MONGODB_URI:
            raise RuntimeError(
                "MONGODB_URI (or MONGO_URI) is not set. Add it to your environment "
                "(.env locally, or Render/Vercel Environment Variables) with your "
                "MongoDB Atlas connection string."
            )
        # Pass tlsCAFile=certifi.where() to fix Linux/Render SSL handshake failures
        _client_cache["client"] = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=8000,
            maxPoolSize=10,
            tlsCAFile=certifi.where()
        )
    return _client_cache["client"]


def get_db():
    return get_client()[MONGODB_DB_NAME]


def get_nodes_collection():
    return get_db()[NODES_COLLECTION]


def ensure_indexes():
    """Call once (e.g. from a seed script or app startup) to set up indexes."""
    get_nodes_collection().create_index("node_id", unique=True)


# ---------------------------------------------------------------------------
# Normalization: MongoDB documents may carry more fields than the dashboard
# needs, or (for a partially-filled node) fewer. This function guarantees
# every field the API/frontend expects is present with a sane default,
# without ever raising on "extra" or "missing" data.
# ---------------------------------------------------------------------------
DEFAULTS = {
    "node_name": "",
    "location": "",
    "latitude": 0.0,
    "longitude": 0.0,
    "parent_gateway": "GW-01 (Main Gateway)",
    "voltage": 0.0,
    "current": 0.0,
    "power": 0.0,
    "energy_consumption": 0.0,
    "power_factor": 0.0,
    "frequency": 0.0,
    "status": "Offline",
    "last_seen": "",
    "relay_state": "OFF",
    "weather": {},
}

NUMERIC_FIELDS = (
    "latitude", "longitude", "voltage", "current", "power",
    "energy_consumption", "power_factor", "frequency",
)

WEATHER_DEFAULTS = {
    "temperature": None,
    "humidity": None,
    "rain": None,
    "wind_speed": None,
    "weather_condition": None,
    "updated_at": None,
}


def normalize_node(doc: dict) -> dict:
    """Fill in defaults, coerce types, and drop Mongo's internal _id."""
    row = {"node_id": str(doc.get("node_id", "")).strip()}

    for field, default in DEFAULTS.items():
        value = doc.get(field, default)
        row[field] = default if value is None else value

    for field in NUMERIC_FIELDS:
        try:
            row[field] = float(row[field])
        except (TypeError, ValueError):
            row[field] = 0.0

    row["status"] = "Online" if str(row["status"]).lower() == "online" else "Offline"
    row["relay_state"] = "ON" if str(row["relay_state"]).upper() == "ON" else "OFF"

    weather = doc.get("weather") or {}
    row["weather"] = {**WEATHER_DEFAULTS, **weather}

    last_seen = row.get("last_seen")
    if isinstance(last_seen, datetime):
        row["last_seen"] = last_seen.strftime("%Y-%m-%d %H:%M:%S")
    else:
        row["last_seen"] = str(last_seen) if last_seen else ""

    return row


def read_all_nodes() -> list[dict]:
    docs = get_nodes_collection().find({})
    return [normalize_node(d) for d in docs]


def get_node(node_id: str) -> dict | None:
    doc = get_nodes_collection().find_one({"node_id": {"$regex": f"^{node_id}$", "$options": "i"}})
    return normalize_node(doc) if doc else None


def create_node(payload: dict) -> dict:
    """Insert a new node document. Raises ValueError if node_id already exists."""
    payload = dict(payload)
    payload.setdefault("status", "Offline")
    payload.setdefault("relay_state", "OFF")
    payload.setdefault("last_seen", datetime.now(timezone.utc))
    payload.setdefault("parent_gateway", DEFAULTS["parent_gateway"])
    for field in NUMERIC_FIELDS:
        payload.setdefault(field, 0.0)
    payload.setdefault("weather", {})

    try:
        get_nodes_collection().insert_one(payload)
    except DuplicateKeyError:
        raise ValueError(f"Node ID '{payload.get('node_id')}' already exists.")

    return normalize_node(payload)


def update_node(node_id: str, updates: dict) -> dict | None:
    """Patch-style update: only the provided fields are changed."""
    updates = {k: v for k, v in updates.items() if v is not None}
    if not updates:
        return get_node(node_id)

    doc = get_nodes_collection().find_one_and_update(
        {"node_id": {"$regex": f"^{node_id}$", "$options": "i"}},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )
    return normalize_node(doc) if doc else None


def delete_node(node_id: str) -> bool:
    result = get_nodes_collection().delete_one(
        {"node_id": {"$regex": f"^{node_id}$", "$options": "i"}}
    )
    return result.deleted_count > 0


def set_relay_state(node_id: str, state: str) -> dict | None:
    return update_node(node_id, {"relay_state": "ON" if state.upper() == "ON" else "OFF"})


def set_weather(node_id: str, weather: dict) -> dict | None:
    weather = {**weather, "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}
    return update_node(node_id, {"weather": weather})


def get_last_refreshed() -> str:
    """Best-effort 'freshest data' timestamp across all nodes, for the topbar."""
    latest = get_nodes_collection().find_one(sort=[("last_seen", -1)])
    if not latest:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    last_seen = latest.get("last_seen")
    if isinstance(last_seen, datetime):
        return last_seen.strftime("%Y-%m-%d %H:%M:%S")
    return str(last_seen) if last_seen else datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")