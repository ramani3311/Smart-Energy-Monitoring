const SORT_OPTIONS = [
  { value: "power", label: "Power" },
  { value: "energy_consumption", label: "Energy" },
  { value: "voltage", label: "Voltage" },
  { value: "current", label: "Current" },
  { value: "node_id", label: "Node ID" },
  { value: "status", label: "Status" },
];

const FILTERS = [
  { value: "all", label: "All" },
  { value: "online", label: "Online" },
  { value: "offline", label: "Offline" },
  { value: "highest", label: "Highest Consumption" },
  { value: "lowest", label: "Lowest Consumption" },
];

export default function Toolbar({ search, onSearch, sortBy, onSortBy, order, onToggleOrder, filter, onFilter }) {
  return (
    <section className="toolbar">
      <div className="search-box">
        <span className="search-box__icon">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="7" />
            <path d="m21 21-4.35-4.35" />
          </svg>
        </span>
        <input
          type="text"
          placeholder="Search by Node ID, name, or location…"
          value={search}
          onChange={(e) => onSearch(e.target.value)}
        />
      </div>

      <div className="sort-group">
        <select value={sortBy} onChange={(e) => onSortBy(e.target.value)}>
          {SORT_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              Sort: {opt.label}
            </option>
          ))}
        </select>
        <button className="order-toggle" onClick={onToggleOrder} title="Toggle ascending / descending">
          {order === "asc" ? (
            <>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 19V5M5 12l7-7 7 7" />
              </svg>
              Ascending
            </>
          ) : (
            <>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 5v14M5 12l7 7 7-7" />
              </svg>
              Descending
            </>
          )}
        </button>
      </div>

      <div className="filter-chips">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            className={`chip ${filter === f.value ? "active" : ""}`}
            onClick={() => onFilter(f.value)}
          >
            {f.label}
          </button>
        ))}
      </div>
    </section>
  );
}
