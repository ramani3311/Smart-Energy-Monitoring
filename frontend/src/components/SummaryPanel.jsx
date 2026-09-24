export default function SummaryPanel({ summary }) {
  if (!summary) return null;

  const {
    total_nodes,
    online_nodes,
    offline_nodes,
    total_power,
    total_energy,
    highest_consuming,
    lowest_consuming,
  } = summary;

  return (
    <section className="summary-panel">
      <div className="summary-grid">
        <div className="summary-cell">
          <div className="summary-cell__label">Total Nodes</div>
          <div className="summary-cell__value">{total_nodes}</div>
        </div>
        <div className="summary-cell summary-cell--online">
          <div className="summary-cell__label">Online</div>
          <div className="summary-cell__value">{online_nodes}</div>
        </div>
        <div className="summary-cell summary-cell--offline">
          <div className="summary-cell__label">Offline</div>
          <div className="summary-cell__value">{offline_nodes}</div>
        </div>
        <div className="summary-cell summary-cell--power">
          <div className="summary-cell__label">Total Power</div>
          <div className="summary-cell__value">
            {(total_power / 1000).toFixed(2)}
            <span className="summary-cell__unit">kW</span>
          </div>
        </div>
        <div className="summary-cell summary-cell--energy">
          <div className="summary-cell__label">Total Energy Today</div>
          <div className="summary-cell__value">
            {total_energy.toFixed(1)}
            <span className="summary-cell__unit">kWh</span>
          </div>
        </div>
      </div>

      <div className="summary-footnotes">
        <div className="summary-footnote">
          <span className="summary-footnote__tag summary-footnote__tag--high">Highest</span>
          {highest_consuming ? (
            <div className="summary-footnote__body">
              <strong>{highest_consuming.node_id} · {highest_consuming.node_name}</strong>
              <span> — {highest_consuming.power.toFixed(0)} W at {highest_consuming.location}</span>
            </div>
          ) : (
            <span className="summary-footnote__body">No data</span>
          )}
        </div>
        <div className="summary-footnote">
          <span className="summary-footnote__tag summary-footnote__tag--low">Lowest</span>
          {lowest_consuming ? (
            <div className="summary-footnote__body">
              <strong>{lowest_consuming.node_id} · {lowest_consuming.node_name}</strong>
              <span> — {lowest_consuming.power.toFixed(0)} W at {lowest_consuming.location}</span>
            </div>
          ) : (
            <span className="summary-footnote__body">No data</span>
          )}
        </div>
      </div>
    </section>
  );
}
