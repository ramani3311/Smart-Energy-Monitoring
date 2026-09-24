"""
seed_mongo.py

Populates MongoDB with the same 18-node sample dataset the project shipped
with in its Excel prototype stage - useful for a fresh Atlas cluster or for
resetting your demo data.

Usage:
    export MONGODB_URI="mongodb+srv://user:pass@cluster.mongodb.net"
    python seed_mongo.py            # adds/updates the 18 sample nodes
    python seed_mongo.py --wipe     # deletes ALL nodes first, then seeds
"""

import random
import sys
from datetime import datetime, timedelta, timezone

from app import db

random.seed(42)

NODES = [
    ("N-01", "Server Room Node",       "Central Server Room, Block A", 23.2156, 72.6369, "high"),
    ("N-02", "Main Library Node",      "Central Library, 1st Floor",   23.2160, 72.6375, "medium"),
    ("N-03", "Hostel Block A Node",    "Boys Hostel Block A",          23.2148, 72.6390, "medium"),
    ("N-04", "Hostel Block B Node",    "Boys Hostel Block B",          23.2145, 72.6395, "medium"),
    ("N-05", "Girls Hostel Node",      "Girls Hostel, Block C",        23.2140, 72.6400, "medium"),
    ("N-06", "Admin Block Node",       "Administrative Building",      23.2170, 72.6360, "low"),
    ("N-07", "CSE Lab-1 Node",         "CSE Dept, Lab 1",              23.2165, 72.6355, "high"),
    ("N-08", "CSE Lab-2 Node",         "CSE Dept, Lab 2",              23.2166, 72.6356, "high"),
    ("N-09", "Mechanical Workshop",    "Mechanical Engg. Workshop",    23.2180, 72.6340, "high"),
    ("N-10", "Electrical Lab Node",    "EE Dept, Power Lab",           23.2178, 72.6345, "high"),
    ("N-11", "Canteen Node",           "Campus Canteen",               23.2135, 72.6380, "medium"),
    ("N-12", "Auditorium Node",        "Main Auditorium",              23.2190, 72.6330, "low"),
    ("N-13", "Sports Complex Node",    "Indoor Sports Complex",        23.2200, 72.6320, "low"),
    ("N-14", "Parking Lot Node",       "Main Gate Parking Lot",        23.2130, 72.6410, "low"),
    ("N-15", "Civil Lab Node",         "Civil Engg. Dept, Lab",        23.2175, 72.6350, "medium"),
    ("N-16", "Guest House Node",       "Faculty Guest House",          23.2155, 72.6420, "low"),
    ("N-17", "Water Pump House Node",  "Campus Water Pump House",      23.2120, 72.6430, "high"),
    ("N-18", "Street Lighting Node",   "Campus Street Lighting Panel", 23.2110, 72.6440, "medium"),
]

LOAD_PROFILE = {"low": (0.4, 1.6), "medium": (1.6, 3.5), "high": (3.5, 8.5)}
WEATHER_CONDITIONS = ["Clear", "Clouds", "Rain", "Mist", "Wind"]
PARENT_GATEWAY = "GW-01 (Main Gateway)"


def make_doc(node_id, name, location, lat, lon, profile):
    voltage = round(random.uniform(214.0, 238.0), 1)
    current = round(random.uniform(*LOAD_PROFILE[profile]), 2)
    power_factor = round(random.uniform(0.86, 0.99), 2)
    power = round(voltage * current * power_factor, 1)
    frequency = round(random.uniform(49.8, 50.2), 2)
    energy = round((power / 1000) * random.uniform(4, 16), 2)

    is_offline = node_id in ("N-14", "N-18")
    status = "Offline" if is_offline else "Online"
    last_seen = datetime.now(timezone.utc) - timedelta(
        seconds=random.randint(2, 90) if status == "Online" else 0,
        hours=random.randint(3, 30) if status != "Online" else 0,
    )
    relay_state = "OFF" if is_offline else random.choice(["ON", "ON", "ON", "OFF"])
    if relay_state == "OFF" or status == "Offline":
        current, power, power_factor = 0.0, 0.0, 0.0

    return {
        "node_id": node_id,
        "node_name": name,
        "location": location,
        "latitude": lat,
        "longitude": lon,
        "parent_gateway": PARENT_GATEWAY,
        "voltage": voltage,
        "current": current,
        "power": power,
        "energy_consumption": energy,
        "power_factor": power_factor,
        "frequency": frequency,
        "status": status,
        "last_seen": last_seen,
        "relay_state": relay_state,
        "weather": {},  # populated later via the "Refresh weather" button / OpenWeatherMap
    }


def main():
    wipe = "--wipe" in sys.argv
    col = db.get_nodes_collection()
    db.ensure_indexes()

    if wipe:
        deleted = col.delete_many({}).deleted_count
        print(f"Wiped {deleted} existing node(s).")

    upserted = 0
    for n in NODES:
        doc = make_doc(*n)
        col.update_one({"node_id": doc["node_id"]}, {"$set": doc}, upsert=True)
        upserted += 1

    print(f"Seeded/updated {upserted} nodes in database '{db.MONGODB_DB_NAME}'.")


if __name__ == "__main__":
    main()
