"""
relay_controller.py

Orchestrates an ON/OFF request:

    1. Ask the hardware layer (hardware_client.py) to actually switch the
       relay - today this is simulated, later it's a real call to your
       Gateway/LoRa link.
    2. Only if that succeeds, write the new relay_state into MongoDB.

This order matters: the database should reflect reality, not wishes. If the
physical node never got the command, the dashboard should keep showing the
old (true) state and surface the error - not lie about it.
"""

from app import db
from app import hardware_client


def set_relay(node_id: str, state: str) -> tuple[bool, str, dict | None]:
    """Returns (success, message, updated_node_or_None)."""
    node = db.get_node(node_id)
    if node is None:
        return False, f"Node '{node_id}' not found.", None

    if node["status"] != "Online":
        return False, f"Node '{node_id}' is offline and cannot be switched right now.", None

    state = "ON" if state.upper() == "ON" else "OFF"

    hw_ok, hw_message = hardware_client.send_relay_command(node_id, state)
    if not hw_ok:
        return False, f"Hardware did not acknowledge the command: {hw_message}", None

    updated = db.set_relay_state(node_id, state)
    if updated is None:
        return False, "Hardware accepted the command but the database update failed.", None

    return True, f"Node '{node_id}' relay set to {state}. ({hw_message})", updated
