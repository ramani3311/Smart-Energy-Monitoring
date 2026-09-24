import { useEffect, useState } from "react";
import { getNodeDetail, setRelay, refreshWeather, deleteNode } from "../api.js";
import { StatusPill } from "./Badges.jsx";
import NodeFormModal from "./NodeFormModal.jsx";

function KV({ label, value, full }) {
  return (
    <div className={`kv-item ${full ? "kv-item--full" : ""}`}>
      <div className="kv-item__label">{label}</div>
      <div className="kv-item__value">{value}</div>
    </div>
  );
}

const fmt = (v, digits, unit) => (v === null || v === undefined ? "—" : `${v.toFixed(digits)}${unit || ""}`);

export default function NodeDetailDrawer({ nodeId, onClose, onRelayChanged, onNodeChanged, onNodeDeleted }) {
  const [node, setNode] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [switching, setSwitching] = useState(false);
  const [controlError, setControlError] = useState(null);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [weatherError, setWeatherError] = useState(null);
  const [showEdit, setShowEdit] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const load = () => {
    setLoading(true);
    setError(null);
    getNodeDetail(nodeId)
      .then(setNode)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodeId]);

  const handleToggleRelay = async () => {
    if (!node) return;
    const nextState = node.relay_state === "ON" ? "OFF" : "ON";
    setSwitching(true);
    setControlError(null);
    try {
      await setRelay(node.node_id, nextState);
      await new Promise((r) => setTimeout(r, 250));
      load();
      onRelayChanged && onRelayChanged();
    } catch (e) {
      setControlError(e.message);
    } finally {
      setSwitching(false);
    }
  };

  const handleRefreshWeather = async () => {
    if (!node) return;
    setWeatherLoading(true);
    setWeatherError(null);
    try {
      await refreshWeather(node.node_id);
      load();
    } catch (e) {
      setWeatherError(e.message);
    } finally {
      setWeatherLoading(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await deleteNode(node.node_id);
      onNodeDeleted && onNodeDeleted();
      onClose();
    } catch (e) {
      setControlError(e.message);
      setDeleting(false);
    }
  };

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer__header">
          <div>
            <h2>{node ? node.node_name : nodeId}</h2>
            <p>{node ? `${node.node_id} · ${node.location}` : "Loading node…"}</p>
          </div>
          <div className="drawer__header-actions">
            {node && (
              <>
                <button className="drawer__icon-btn" title="Edit node" onClick={() => setShowEdit(true)}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 20h9M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5Z" />
                  </svg>
                </button>
                <button className="drawer__icon-btn drawer__icon-btn--danger" title="Delete node" onClick={() => setConfirmDelete(true)}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0-1 14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2L4 6h16Z" />
                  </svg>
                </button>
              </>
            )}
            <button className="drawer__close" onClick={onClose} aria-label="Close">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6 6 18M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {loading && <div className="drawer__loading">Loading node data…</div>}
        {error && <div className="drawer__error">Could not load node: {error}</div>}

        {node && !loading && !error && (
          <>
            <div className="drawer__body">
              <div className="drawer__section">
                <div className="drawer__section-title">Status</div>
                <StatusPill status={node.status} />
                <div style={{ marginTop: 10 }}>
                  <KV label="Last Seen" value={node.last_seen || "—"} full />
                </div>
              </div>

              <div className="drawer__section">
                <div className="drawer__section-title">Electrical</div>
                <div className="kv-grid">
                  <KV label="Voltage" value={fmt(node.voltage, 1, " V")} />
                  <KV label="Current" value={fmt(node.current, 2, " A")} />
                  <KV label="Power" value={fmt(node.power, 1, " W")} />
                  <KV label="Energy" value={fmt(node.energy_consumption, 2, " kWh")} />
                  <KV label="Frequency" value={fmt(node.frequency, 2, " Hz")} />
                  <KV label="Power Factor" value={fmt(node.power_factor, 2, "")} />
                </div>
              </div>

              <div className="drawer__section">
                <div className="drawer__section-title">Node Information</div>
                <div className="kv-grid">
                  <KV label="Node ID" value={node.node_id} />
                  <KV label="Parent Gateway" value={node.parent_gateway} />
                  <KV label="Location" value={node.location} full />
                  <KV label="Latitude" value={fmt(node.latitude, 4, "")} />
                  <KV label="Longitude" value={fmt(node.longitude, 4, "")} />
                </div>
              </div>

              <div className="drawer__section">
                <div className="drawer__section-title drawer__section-title--with-action">
                  Weather at Node Location
                  <button className="link-btn" onClick={handleRefreshWeather} disabled={weatherLoading}>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 12a9 9 0 1 1-3-6.7" />
                      <path d="M21 3v6h-6" />
                    </svg>
                    {weatherLoading ? "Refreshing…" : "Refresh"}
                  </button>
                </div>
                {weatherError && <div className="relay-error" style={{ marginBottom: 10 }}>{weatherError}</div>}
                <div className="kv-grid">
                  <KV label="Temperature" value={fmt(node.weather.temperature, 1, " °C")} />
                  <KV label="Humidity" value={fmt(node.weather.humidity, 0, " %")} />
                  <KV label="Rain" value={fmt(node.weather.rain, 1, " mm")} />
                  <KV label="Wind Speed" value={fmt(node.weather.wind_speed, 1, " km/h")} />
                  <KV label="Condition" value={node.weather.weather_condition || "Not fetched yet"} full />
                </div>
                {node.weather.updated_at && (
                  <div className="relay-note" style={{ marginTop: 8 }}>Last fetched: {node.weather.updated_at}</div>
                )}
              </div>
            </div>

            <div className="drawer__footer">
              <div className="relay-control">
                <div className="relay-control__label">
                  Relay is currently <strong>{node.relay_state}</strong>.
                </div>
                <button
                  className={`relay-btn ${node.relay_state === "ON" ? "relay-btn--off" : "relay-btn--on"}`}
                  onClick={handleToggleRelay}
                  disabled={switching || node.status !== "Online"}
                >
                  {switching ? "Switching…" : node.relay_state === "ON" ? "TURN OFF" : "TURN ON"}
                </button>
              </div>
              {node.status !== "Online" && (
                <div className="relay-note">This node is offline — control is disabled until it reconnects.</div>
              )}
              {controlError && <div className="relay-error">{controlError}</div>}
              <div className="relay-note">
                Control path: Dashboard → Backend → Gateway → LoRa → Child Node, then MongoDB is updated
                only after the hardware acknowledges.
              </div>
            </div>
          </>
        )}
      </div>

      {showEdit && node && (
        <NodeFormModal
          mode="edit"
          initialData={node}
          onClose={() => setShowEdit(false)}
          onSaved={() => {
            setShowEdit(false);
            load();
            onNodeChanged && onNodeChanged();
          }}
        />
      )}

      {confirmDelete && (
        <div className="modal-overlay" onClick={() => setConfirmDelete(false)}>
          <div className="confirm-box" onClick={(e) => e.stopPropagation()}>
            <h3>Remove {node?.node_id}?</h3>
            <p>This deletes the node from the database. This can't be undone.</p>
            <div className="modal__footer">
              <button className="btn-secondary" onClick={() => setConfirmDelete(false)}>Cancel</button>
              <button className="btn-danger" onClick={handleDelete} disabled={deleting}>
                {deleting ? "Removing…" : "Remove Node"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
