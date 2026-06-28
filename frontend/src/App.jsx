import { useState } from "react";
import Logo from "./components/Logo.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Datasets from "./pages/Datasets.jsx";
import RunEval from "./pages/RunEval.jsx";
import Results from "./pages/Results.jsx";
import Logs from "./pages/Logs.jsx";

const TABS = [
  { id: "dashboard", label: "Overview" },
  { id: "datasets", label: "Datasets" },
  { id: "run", label: "Run" },
  { id: "results", label: "Results" },
  { id: "logs", label: "Logs" },
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
        <div className="header-inner">
          <div className="brand">
            <Logo size={26} />
            <h1>LLM Eval</h1>
          </div>
          <nav className="nav-tabs" aria-label="Main">
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
        </div>
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
        {activeTab === "logs" && <Logs />}
      </main>

      <footer className="app-footer">
        <div className="footer-inner">
          <a href={GITHUB_URL} target="_blank" rel="noreferrer">
            GitHub
          </a>
          <a href={`${API_URL}/docs`} target="_blank" rel="noreferrer">
            API
          </a>
        </div>
      </footer>
    </div>
  );
}