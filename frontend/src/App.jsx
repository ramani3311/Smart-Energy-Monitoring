import { useEffect, useState, useCallback } from "react";
import TopBar from "./components/TopBar.jsx";
import SummaryPanel from "./components/SummaryPanel.jsx";
import Toolbar from "./components/Toolbar.jsx";
import NodeTable from "./components/NodeTable.jsx";
import NodeDetailDrawer from "./components/NodeDetailDrawer.jsx";
import NodeFormModal from "./components/NodeFormModal.jsx";
import { getSummary, getNodes } from "./api.js";

const AUTO_REFRESH_MS = 15000;

export default function App() {
  const [summary, setSummary] = useState(null);
  const [nodes, setNodes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState("power");
  const [order, setOrder] = useState("desc");
  const [filter, setFilter] = useState("all");

  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [showAddNode, setShowAddNode] = useState(false);

  const loadData = useCallback(async (isManual = false) => {
    if (isManual) setRefreshing(true);
    try {
      const [summaryData, nodesData] = await Promise.all([
        getSummary(),
        getNodes({ search, sortBy, order, filter }),
      ]);
      setSummary(summaryData);
      setNodes(nodesData);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
      if (isManual) setRefreshing(false);
    }
  }, [search, sortBy, order, filter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    const id = setInterval(() => loadData(false), AUTO_REFRESH_MS);
    return () => clearInterval(id);
  }, [loadData]);

  if (loading) {
    return (
      <div className="app">
        <div className="app-loading">Connecting to gateway…</div>
      </div>
    );
  }

  if (error && !summary) {
    return (
      <div className="app">
        <div className="app-error">
          <strong>Could not reach the backend / database</strong>
          <span>{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <TopBar
        lastRefreshed={summary?.last_refreshed}
        onRefresh={() => loadData(true)}
        refreshing={refreshing}
        onAddNode={() => setShowAddNode(true)}
      />
      <main className="main">
        <SummaryPanel summary={summary} />
        <Toolbar
          search={search}
          onSearch={setSearch}
          sortBy={sortBy}
          onSortBy={setSortBy}
          order={order}
          onToggleOrder={() => setOrder((o) => (o === "asc" ? "desc" : "asc"))}
          filter={filter}
          onFilter={setFilter}
        />
        <NodeTable nodes={nodes} onSelectNode={setSelectedNodeId} />
      </main>

      {selectedNodeId && (
        <NodeDetailDrawer
          nodeId={selectedNodeId}
          onClose={() => setSelectedNodeId(null)}
          onRelayChanged={() => loadData(false)}
          onNodeChanged={() => loadData(false)}
          onNodeDeleted={() => loadData(false)}
        />
      )}

      {showAddNode && (
        <NodeFormModal
          mode="create"
          onClose={() => setShowAddNode(false)}
          onSaved={() => {
            setShowAddNode(false);
            loadData(true);
          }}
        />
      )}
    </div>
  );
}
