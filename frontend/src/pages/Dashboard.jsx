import { useEffect, useState } from "react";
import { fetchHealth, fetchStats, getApiBaseUrl } from "../api/client.js";

const API_BASE_URL = getApiBaseUrl();

export default function Dashboard() {
  const [health, setHealth] = useState(null);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [healthData, statsData] = await Promise.all([fetchHealth(), fetchStats()]);
        if (!cancelled) {
          setHealth(healthData);
          setStats(statsData);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
          setHealth(null);
          setStats(null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="card">
      <h2>Dashboard</h2>
      <p className="card-description">
        Production eval workspace. Upload datasets, run prompt evaluations against
        real models, and track pass rate over time.
      </p>

      <div className="status-grid">
        <div className="status-item">
          <span className="label">API</span>
          <span className="value mono">{API_BASE_URL}</span>
        </div>
      </div>

      {loading && <p className="status-text">Loading system status...</p>}

      {error && (
        <div className="alert alert-error">
          <strong>API unreachable.</strong> {error}
        </div>
      )}

      {health && (
        <>
          <div className="metrics-grid">
            <div className="metric">
              <span className="label">System</span>
              <span className={`value badge ${health.status === "ok" ? "badge-ok" : "badge-warn"}`}>
                {health.status}
              </span>
            </div>
            <div className="metric">
              <span className="label">Database</span>
              <span className="value">{health.database}</span>
            </div>
            <div className="metric">
              <span className="label">Environment</span>
              <span className="value">{health.environment}</span>
            </div>
            <div className="metric">
              <span className="label">Gemini</span>
              <span className="value">
                {health.llm_providers?.gemini ? "configured" : "not set"}
              </span>
            </div>
            <div className="metric">
              <span className="label">Groq</span>
              <span className="value">
                {health.llm_providers?.groq ? "configured" : "not set"}
              </span>
            </div>
            <div className="metric">
              <span className="label">OpenAI</span>
              <span className="value">
                {health.llm_providers?.openai ? "configured" : "not set"}
              </span>
            </div>
          </div>

          {stats && (
            <div className="metrics-grid">
              <div className="metric">
                <span className="label">Datasets</span>
                <span className="value">{stats.dataset_count}</span>
              </div>
              <div className="metric">
                <span className="label">Total runs</span>
                <span className="value">{stats.run_count}</span>
              </div>
              <div className="metric">
                <span className="label">Latest pass rate</span>
                <span className="value">
                  {stats.latest_pass_rate != null
                    ? `${(stats.latest_pass_rate * 100).toFixed(1)}%`
                    : "—"}
                </span>
              </div>
              <div className="metric">
                <span className="label">Latest avg score</span>
                <span className="value">
                  {stats.latest_average_score != null
                    ? stats.latest_average_score.toFixed(2)
                    : "—"}
                </span>
              </div>
            </div>
          )}

          {health.status === "degraded" && (
            <div className="alert alert-warn">
              <strong>Degraded mode.</strong> Add <code>GEMINI_API_KEY</code> on the
              backend (recommended on Render). Groq often fails on cloud hosts.
            </div>
          )}
        </>
      )}
    </section>
  );
}