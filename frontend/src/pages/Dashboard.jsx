import { useCallback, useEffect, useState } from "react";
import { fetchHealth, fetchStats, getApiBaseUrl } from "../api/client.js";

export default function Dashboard({ onNavigate }) {
  const [health, setHealth] = useState(null);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [healthData, statsData] = await Promise.all([fetchHealth(), fetchStats()]);
      setHealth(healthData);
      setStats(statsData);
    } catch (err) {
      setError(err.message);
      setHealth(null);
      setStats(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <section className="card">
      <h2>Dashboard</h2>
      <p className="card-description">
        System health, provider configuration, and eval history at a glance.
      </p>

      <div className="status-grid">
        <div className="status-item">
          <span className="label">API endpoint</span>
          <span className="value mono">{getApiBaseUrl()}</span>
        </div>
      </div>

      {loading && <p className="status-text">Checking backend status...</p>}

      {error && (
        <div className="alert alert-error">
          <strong>Backend unreachable.</strong> {error}
          <p className="hint">
            Render&apos;s free tier sleeps after inactivity. Wait ~30 seconds, then retry.
          </p>
          <button type="button" className="btn btn-secondary btn-sm" onClick={load}>
            Retry connection
          </button>
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
              <strong>Degraded mode.</strong> Set <code>GEMINI_API_KEY</code> on Render for
              live inference. Groq is often blocked from cloud hosts.
            </div>
          )}

          <div className="quick-start">
            <h3>Quick start</h3>
            <ol>
              <li>
                Open <button type="button" className="btn-inline" onClick={() => onNavigate?.("datasets")}>Datasets</button> — upload a CSV or use the seeded <code>sample</code> set.
              </li>
              <li>
                Go to <button type="button" className="btn-inline" onClick={() => onNavigate?.("run")}>Run eval</button> — pick a model and prompt template.
              </li>
              <li>
                Review scores on <button type="button" className="btn-inline" onClick={() => onNavigate?.("results")}>Results</button>.
              </li>
            </ol>
          </div>
        </>
      )}
    </section>
  );
}