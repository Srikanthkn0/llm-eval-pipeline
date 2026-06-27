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

const GITHUB_URL = "https://github.com/Srikanthkn0/llm-eval-pipeline";
const API_URL = "https://llm-eval-pipeline-api.onrender.com";

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [selectedRunId, setSelectedRunId] = useState(null);

  function navigate(tab) {
    setActiveTab(tab);
  }

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
            <p className="subtitle">
              CSV test suites, async eval jobs, and pass-rate tracking for prompt changes
            </p>
          </div>
        </div>
        <nav className="nav-tabs" aria-label="Main navigation">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={`nav-tab ${activeTab === tab.id ? "nav-tab-active" : ""}`}
              onClick={() => navigate(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </header>
      <main className="app-main">
        {activeTab === "dashboard" && <Dashboard onNavigate={navigate} />}
        {activeTab === "datasets" && <Datasets />}
        {activeTab === "run" && (
          <RunEval onRunComplete={handleRunComplete} onNavigate={navigate} />
        )}
        {activeTab === "results" && (
          <Results selectedRunId={selectedRunId} onSelectRun={setSelectedRunId} />
        )}
      </main>
      <footer className="app-footer">
        <a href={GITHUB_URL} target="_blank" rel="noreferrer">
          Source
        </a>
        <span className="footer-sep">·</span>
        <a href={`${API_URL}/docs`} target="_blank" rel="noreferrer">
          API docs
        </a>
        <span className="footer-sep">·</span>
        <a href="https://llm-eval-pipeline.vercel.app" target="_blank" rel="noreferrer">
          Live demo
        </a>
      </footer>
    </div>
  );
}