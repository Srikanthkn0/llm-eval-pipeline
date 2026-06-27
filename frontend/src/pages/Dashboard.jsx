import { useEffect, useState } from "react";
import { fetchHealth } from "../api/client.js";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export default function Dashboard() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function loadHealth() {
      try {
        const data = await fetchHealth();
        if (!cancelled) {
          setHealth(data);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
          setHealth(null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadHealth();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="card">
      <h2>Dashboard</h2>
      <p className="card-description">
        Upload CSV test cases, run them through a prompt template, and review
        pass rate, per-case scores, and latency. CI runs the same eval flow on
        every push.
      </p>

      <div className="status-grid">
        <div className="status-item">
          <span className="label">API base URL</span>
          <span className="value mono">{API_BASE_URL}</span>
        </div>
      </div>

      {loading && <p className="status-text">Checking API...</p>}

      {error && (
        <div className="alert alert-error">
          <strong>API unreachable.</strong> {error}
          <p className="hint">
            Start the backend with <code>uvicorn app.main:app --reload --port 8000</code>{" "}
            or set <code>VITE_API_BASE_URL</code> to your deployed API.
          </p>
        </div>
      )}

      {health && (
        <div className="status-grid">
          <div className="status-item">
            <span className="label">Status</span>
            <span className="value badge badge-ok">{health.status}</span>
          </div>
          <div className="status-item">
            <span className="label">App</span>
            <span className="value">{health.app_name}</span>
          </div>
          <div className="status-item">
            <span className="label">Environment</span>
            <span className="value">{health.environment}</span>
          </div>
        </div>
      )}
    </section>
  );
}