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
      <section className="hero-card">
        <div className="hero-content">
          <h2>Production-ready LLM evaluation</h2>
          <p>
            Upload datasets, run evals across providers, and block prompt injections with a hybrid
            guard — rule engine plus ML classifier. Full request logging built in.
          </p>
          <div className="pill-row">
            <span className="pill">Hybrid guard</span>
            <span className="pill pill-secondary">Multi-provider</span>
            <span className="pill">Request logs</span>
            <span className="pill pill-secondary">Rate limits</span>
          </div>
        </div>
      </section>

      <div className="feature-grid">
        <div className="feature-card">
          <h4>ML + rules guard</h4>
          <p>40+ input rules and a trained classifier catch paraphrased injections rules miss.</p>
        </div>
        <div className="feature-card">
          <h4>Provider adapters</h4>
          <p>Gemini, Groq, OpenAI-compatible APIs with consistent request/response shape.</p>
        </div>
        <div className="feature-card">
          <h4>Observability</h4>
          <p>SQLite request logs, pass/fail stats, latency tracking, and trace IDs per eval.</p>
        </div>
      </div>

      <header className="page-header">
        <h2>System overview</h2>
        <p>Live health check and aggregate stats from the API.</p>
      </header>

      <section className="card">
        {loading && <p className="status-text">Connecting to API...</p>}

        {error && (
          <div className="alert alert-error">
            <strong>Can&apos;t reach backend.</strong> {error}
            <p className="hint">Render free tier sleeps after idle. Wait ~30s, then retry.</p>
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
              <div className="stat">
                <span className="stat-label">Requests</span>
                <span className="stat-value">{stats?.total_requests ?? 0}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Req pass rate</span>
                <span className="stat-value">
                  {stats?.request_pass_rate != null
                    ? `${(stats.request_pass_rate * 100).toFixed(1)}%`
                    : "—"}
                </span>
              </div>
            </div>

            <h3>Infrastructure</h3>
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
                  {health.llm_providers?.gemini ? "configured" : "—"}
                </span>
              </div>
              <div className="status-list-item">
                <span className="label">Groq</span>
                <span className="value">
                  {health.llm_providers?.groq ? "configured" : "—"}
                </span>
              </div>
              <div className="status-list-item">
                <span className="label">OpenAI</span>
                <span className="value">
                  {health.llm_providers?.openai ? "configured" : "—"}
                </span>
              </div>
            </div>

            {health.status === "degraded" && (
              <div className="alert alert-warn">
                No LLM configured. Set <code>GEMINI_API_KEY</code> on Render or{" "}
                <code>ALLOW_MOCK_MODEL=true</code>.
              </div>
            )}

            {health.llm_providers?.mock_allowed && !health.llm_providers?.gemini && (
              <div className="alert alert-warn">
                Running on <code>mock-model-v1</code> — fixed answers, no API calls. Add{" "}
                <code>GEMINI_API_KEY</code> for live inference.
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