"""
hardware_client.py

Represents the "Backend -> Gateway -> LoRa -> Child Node" leg of the
architecture. The dashboard's backend usually runs in the cloud (Vercel),
while the physical Gateway (Raspberry Pi + LoRa radio) sits on-site. This
module is how the two talk.

HARDWARE_MODE controls behaviour (env var):
  - "none"     (default) - no physical gateway yet. Commands are logged and
                treated as successful immediately, so the UI keeps working
                end-to-end while you build the hardware side.
  - "webhook"  - the Gateway runs its own small HTTP listener (e.g. a tiny
                Flask/FastAPI service on the Pi, reachable via a static IP,
                DDNS hostname, or a tunnel like Cloudflare Tunnel/ngrok).
                Set GATEWAY_WEBHOOK_URL to that listener's relay endpoint,
                e.g. https://my-gateway.example.com/relay
                Optionally set GATEWAY_API_KEY - sent as
                "Authorization: Bearer <key>" so only your dashboard backend
                can command the gateway.

The Gateway-side listener is NOT part of this project (it runs on the Pi
next to the LoRa radio) - implement it however suits your radio module
(e.g. pyLoRa, RFM95 SPI driver, or a vendor SDK). It just needs to accept:
    POST /relay   { "node_id": "N-01", "state": "ON" }
and translate that into an actual LoRa packet to the child node, then
respond 200 on success.
"""

import os
import logging

import requests

logger = logging.getLogger("hardware_client")

HARDWARE_MODE = os.environ.get("HARDWARE_MODE", "none").lower()
GATEWAY_WEBHOOK_URL = os.environ.get("GATEWAY_WEBHOOK_URL", "")
GATEWAY_API_KEY = os.environ.get("GATEWAY_API_KEY", "")
GATEWAY_TIMEOUT_SECONDS = float(os.environ.get("GATEWAY_TIMEOUT_SECONDS", "6"))


def send_relay_command(node_id: str, state: str) -> tuple[bool, str]:
    """
    Send an ON/OFF command toward the real hardware.
    Returns (success, message). The caller (relay_controller.py) only
    updates MongoDB's relay_state after this returns success=True, so the
    database never claims a state the hardware didn't actually reach.
    """
    if HARDWARE_MODE == "webhook":
        return _send_via_webhook(node_id, state)

    # Default: no gateway wired up yet - simulate a successful ack so the
    # rest of the app (and your demo) keeps working.
    logger.info("[simulated hardware] would send node=%s state=%s", node_id, state)
    return True, f"Simulated: no gateway configured (HARDWARE_MODE=none). Set HARDWARE_MODE=webhook to go live."


def _send_via_webhook(node_id: str, state: str) -> tuple[bool, str]:
    if not GATEWAY_WEBHOOK_URL:
        return False, "HARDWARE_MODE=webhook but GATEWAY_WEBHOOK_URL is not set."

    headers = {"Content-Type": "application/json"}
    if GATEWAY_API_KEY:
        headers["Authorization"] = f"Bearer {GATEWAY_API_KEY}"

    try:
        resp = requests.post(
            GATEWAY_WEBHOOK_URL,
            json={"node_id": node_id, "state": state},
            headers=headers,
            timeout=GATEWAY_TIMEOUT_SECONDS,
        )
        if resp.status_code >= 200 and resp.status_code < 300:
            return True, f"Gateway acknowledged: {resp.status_code}"
        return False, f"Gateway rejected the command: HTTP {resp.status_code} - {resp.text[:200]}"
    except requests.exceptions.RequestException as e:
        return False, f"Could not reach gateway at {GATEWAY_WEBHOOK_URL}: {e}"
