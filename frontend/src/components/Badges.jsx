export function StatusPill({ status }) {
  const online = status === "Online";
  return (
    <span className={`status-pill ${online ? "status-pill--online" : "status-pill--offline"}`}>
      <span className={`status-dot ${online ? "status-dot--online" : ""}`} />
      {status}
    </span>
  );
}

export function RelayBadge({ state }) {
  const on = state === "ON";
  return <span className={`relay-badge ${on ? "relay-badge--on" : "relay-badge--off"}`}>{on ? "● ON" : "○ OFF"}</span>;
}
