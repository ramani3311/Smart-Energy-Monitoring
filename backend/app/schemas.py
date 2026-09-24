"""Pydantic request/response models for the Smart Energy Dashboard API."""

from typing import Optional

from pydantic import BaseModel, Field


class WeatherInfo(BaseModel):
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    rain: Optional[float] = None
    wind_speed: Optional[float] = None
    weather_condition: Optional[str] = None
    updated_at: Optional[str] = None


class NodeSummary(BaseModel):
    """Lightweight representation used for the main table/list view."""

    node_id: str
    node_name: str
    location: str
    voltage: float
    current: float
    power: float
    energy_consumption: float
    power_factor: float
    status: str
    relay_state: str
    last_seen: str


class NodeDetail(NodeSummary):
    """Full representation used for the node detail drawer."""

    latitude: float
    longitude: float
    parent_gateway: str
    frequency: float
    weather: WeatherInfo


class DashboardSummary(BaseModel):
    total_nodes: int
    online_nodes: int
    offline_nodes: int
    total_power: float
    total_energy: float
    highest_consuming: Optional[NodeSummary] = None
    lowest_consuming: Optional[NodeSummary] = None
    last_refreshed: str


class RelayControlRequest(BaseModel):
    state: str  # "ON" or "OFF"


class RelayControlResponse(BaseModel):
    node_id: str
    relay_state: str
    success: bool
    message: str


# ---------------------------------------------------------------------------
# Node management (Add / Edit / Remove)
# ---------------------------------------------------------------------------
class NodeCreate(BaseModel):
    """
    Fields needed to register a new node. Electrical readings are left out
    here on purpose - those come from the sensor/gateway once the node is
    actually live, not typed in by hand.
    """

    node_id: str = Field(..., min_length=1)
    node_name: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)
    latitude: float
    longitude: float
    parent_gateway: Optional[str] = "GW-01 (Main Gateway)"
    status: Optional[str] = "Offline"


class NodeUpdate(BaseModel):
    """
    Patch-style update - every field optional, only the ones provided are
    changed. Covers both admin edits (name/location/coordinates) and
    telemetry updates (voltage/power/etc.) if you later feed those in via
    an API call from the gateway instead of by hand.
    """

    node_name: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    parent_gateway: Optional[str] = None
    voltage: Optional[float] = None
    current: Optional[float] = None
    power: Optional[float] = None
    energy_consumption: Optional[float] = None
    power_factor: Optional[float] = None
    frequency: Optional[float] = None
    status: Optional[str] = None


class DeleteResponse(BaseModel):
    node_id: str
    deleted: bool
    message: str


class WeatherRefreshResponse(BaseModel):
    node_id: str
    weather: WeatherInfo
    message: str
