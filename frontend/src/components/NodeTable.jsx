import { StatusPill, RelayBadge } from "./Badges.jsx";

export default function NodeTable({ nodes, onSelectNode }) {
  if (!nodes.length) {
    return (
      <div className="table-wrap">
        <div className="empty-state">
          <strong>No nodes match this view</strong>
          Try clearing the search box or switching filters.
        </div>
      </div>
    );
  }

  return (
    <div className="table-wrap">
      <table className="node-table">
        <thead>
          <tr>
            <th>Node ID</th>
            <th>Name / Location</th>
            <th>Voltage</th>
            <th>Current</th>
            <th>Power</th>
            <th>Energy</th>
            <th>Status</th>
            <th>Relay</th>
          </tr>
        </thead>
        <tbody>
          {nodes.map((n) => (
            <tr key={n.node_id} onClick={() => onSelectNode(n.node_id)}>
              <td className="td-mono">{n.node_id}</td>
              <td>
                <div className="td-name">{n.node_name}</div>
                <div className="td-sub">{n.location}</div>
              </td>
              <td className="td-mono">{n.voltage.toFixed(1)} V</td>
              <td className="td-mono">{n.current.toFixed(2)} A</td>
              <td className="td-mono">{n.power.toFixed(0)} W</td>
              <td className="td-mono">{n.energy_consumption.toFixed(2)} kWh</td>
              <td><StatusPill status={n.status} /></td>
              <td><RelayBadge state={n.relay_state} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
