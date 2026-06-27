import { useState } from "react";
import Dashboard from "./pages/Dashboard.jsx";
import Datasets from "./pages/Datasets.jsx";
import RunEval from "./pages/RunEval.jsx";
import Results from "./pages/Results.jsx";

const TABS = [
  { id: "dashboard", label: "Dashboard" },
  { id: "datasets", label: "Datasets" },
  { id: "run", label: "Run eval" },
  { id: "results", label: "Results" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [selectedRunId, setSelectedRunId] = useState(null);

  function handleRunComplete(runId) {
    setSelectedRunId(runId);
    setActiveTab("results");
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-top">
          <div>
            <h1>LLM Eval Pipeline</h1>
            <p className="subtitle">Run prompt evaluations against saved datasets</p>
          </div>
        </div>
        <nav className="nav-tabs">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={`nav-tab ${activeTab === tab.id ? "nav-tab-active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </header>
      <main className="app-main">
        {activeTab === "dashboard" && <Dashboard />}
        {activeTab === "datasets" && <Datasets />}
        {activeTab === "run" && <RunEval onRunComplete={handleRunComplete} />}
        {activeTab === "results" && (
          <Results
            selectedRunId={selectedRunId}
            onSelectRun={setSelectedRunId}
          />
        )}
      </main>
    </div>
  );
}
