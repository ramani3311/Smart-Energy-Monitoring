import { useState } from "react";
import { createNode, updateNode } from "../api.js";

const emptyForm = {
  node_id: "",
  node_name: "",
  location: "",
  latitude: "",
  longitude: "",
  parent_gateway: "GW-01 (Main Gateway)",
  status: "Offline",
};

export default function NodeFormModal({ mode, initialData, onClose, onSaved }) {
  const isEdit = mode === "edit";
  const [form, setForm] = useState(
    isEdit && initialData
      ? {
          node_id: initialData.node_id,
          node_name: initialData.node_name,
          location: initialData.location,
          latitude: initialData.latitude,
          longitude: initialData.longitude,
          parent_gateway: initialData.parent_gateway,
          status: initialData.status,
        }
      : emptyForm
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload = {
        node_name: form.node_name.trim(),
        location: form.location.trim(),
        latitude: parseFloat(form.latitude),
        longitude: parseFloat(form.longitude),
        parent_gateway: form.parent_gateway.trim(),
        status: form.status,
      };
      if (Number.isNaN(payload.latitude) || Number.isNaN(payload.longitude)) {
        throw new Error("Latitude and Longitude must be valid numbers.");
      }

      if (isEdit) {
        await updateNode(form.node_id, payload);
      } else {
        if (!form.node_id.trim()) throw new Error("Node ID is required.");
        await createNode({ ...payload, node_id: form.node_id.trim() });
      }
      onSaved();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <h2>{isEdit ? "Edit Node" : "Add New Node"}</h2>
          <button className="drawer__close" onClick={onClose} aria-label="Close">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal__body">
          <div className="form-row">
            <label>Node ID</label>
            <input
              value={form.node_id}
              onChange={update("node_id")}
              placeholder="e.g. N-19"
              disabled={isEdit}
              required
            />
          </div>

          <div className="form-row">
            <label>Node Name</label>
            <input value={form.node_name} onChange={update("node_name")} placeholder="e.g. Physics Lab Node" required />
          </div>

          <div className="form-row">
            <label>Location</label>
            <input value={form.location} onChange={update("location")} placeholder="e.g. Physics Dept, Lab 1" required />
          </div>

          <div className="form-grid">
            <div className="form-row">
              <label>Latitude</label>
              <input type="number" step="any" value={form.latitude} onChange={update("latitude")} required />
            </div>
            <div className="form-row">
              <label>Longitude</label>
              <input type="number" step="any" value={form.longitude} onChange={update("longitude")} required />
            </div>
          </div>

          <div className="form-row">
            <label>Parent Gateway</label>
            <input value={form.parent_gateway} onChange={update("parent_gateway")} />
          </div>

          <div className="form-row">
            <label>Status</label>
            <select value={form.status} onChange={update("status")}>
              <option value="Offline">Offline</option>
              <option value="Online">Online</option>
            </select>
          </div>

          {error && <div className="relay-error">{error}</div>}

          <div className="modal__footer">
            <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={saving}>
              {saving ? "Saving…" : isEdit ? "Save Changes" : "Add Node"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
