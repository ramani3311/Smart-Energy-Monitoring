export default function TopBar({ lastRefreshed, onRefresh, refreshing, onAddNode }) {
  return (
    <header className="topbar">
      <div className="topbar__brand">
        <div className="topbar__mark">GW</div>
        <div>
          <div className="topbar__title">Smart Energy Monitoring — Gateway Dashboard</div>
          <div className="topbar__subtitle">GW-01 · Main Gateway · LoRa Parent Node</div>
        </div>
      </div>
      <div className="topbar__meta">
        <span>
          Data source: <strong>MongoDB</strong>
        </span>
        <span>
          Last refreshed: <strong>{lastRefreshed || "—"}</strong>
        </span>
        <button className="btn-add-node" onClick={onAddNode} title="Register a new node">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 5v14M5 12h14" />
          </svg>
          Add Node
        </button>
        <button
          className={`btn-refresh ${refreshing ? "spinning" : ""}`}
          onClick={onRefresh}
          title="Reload data from Excel"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 12a9 9 0 1 1-3-6.7" />
            <path d="M21 3v6h-6" />
          </svg>
          Refresh
        </button>
      </div>
    </header>
  );
}
