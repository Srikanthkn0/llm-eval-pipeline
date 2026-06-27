import { useCallback, useEffect, useState } from "react";
import { fetchHealth, fetchStats, getApiBaseUrl } from "../api/client.js";

function StatusDot({ ok, warn }) {
  const cls = ok ? "dot-ok" : warn ? "dot-warn" : "dot-muted";
  return <span className={`dot ${cls}`} aria-hidden="true" />;
}

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
    <div className="stack">
      <header className="page-header">
        <h2>Overview</h2>
        <p>Backend status and eval history.</p>
      </header>

      <section className="card">
        {loading && <p className="status-text">Connecting…</p>}

        {error && (
          <div className="alert alert-error">
            <strong>Can&apos;t reach backend.</strong> {error}
            <p className="hint">Render free tier sleeps after idle — wait ~30s, then retry.</p>
            <button type="button" className="btn btn-secondary btn-sm" onClick={load}>
              Retry
            </button>
          </div>
        )}

        {health && (
          <>
            <div className="stat-row">
              <div className="stat">
                <span className="stat-label">Pass rate</span>
                <span className="stat-value stat-value-lg">
                  {stats?.latest_pass_rate != null
                    ? `${(stats.latest_pass_rate * 100).toFixed(1)}%`
                    : "—"}
                </span>
              </div>
              <div className="stat">
                <span className="stat-label">Runs</span>
                <span className="stat-value">{stats?.run_count ?? 0}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Datasets</span>
                <span className="stat-value">{stats?.dataset_count ?? 0}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Avg score</span>
                <span className="stat-value">
                  {stats?.latest_average_score != null
                    ? stats.latest_average_score.toFixed(2)
                    : "—"}
                </span>
              </div>
            </div>

            <h3>System</h3>
            <div className="status-list">
              <div className="status-list-item">
                <span className="label">API</span>
                <span className="value mono">{getApiBaseUrl()}</span>
              </div>
              <div className="status-list-item">
                <span className="label">Status</span>
                <span className="value">
                  <StatusDot ok={health.status === "ok"} warn={health.status === "degraded"} />
                  {health.status}
                </span>
              </div>
              <div className="status-list-item">
                <span className="label">Database</span>
                <span className="value">{health.database}</span>
              </div>
              <div className="status-list-item">
                <span className="label">Gemini</span>
                <span className="value">
                  {health.llm_providers?.gemini ? "yes" : "no"}
                </span>
              </div>
              <div className="status-list-item">
                <span className="label">Groq</span>
                <span className="value">
                  {health.llm_providers?.groq ? "yes" : "no"}
                </span>
              </div>
              <div className="status-list-item">
                <span className="label">OpenAI</span>
                <span className="value">
                  {health.llm_providers?.openai ? "yes" : "no"}
                </span>
              </div>
            </div>

            {health.status === "degraded" && (
              <div className="alert alert-warn">
                No LLM key configured. Set <code>GEMINI_API_KEY</code> on Render.
              </div>
            )}

            <p className="section-note">
              Upload a CSV on{" "}
              <button type="button" className="btn-inline" onClick={() => onNavigate?.("datasets")}>
                Datasets
              </button>
              , run on{" "}
              <button type="button" className="btn-inline" onClick={() => onNavigate?.("run")}>
                Run
              </button>
              . Sample dataset <code>sample</code> is preloaded.
            </p>
          </>
        )}
      </section>
    </div>
  );
}