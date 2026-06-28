import { useCallback, useEffect, useState } from "react";
import { fetchLogs } from "../api/client.js";

function formatTime(iso) {
  if (!iso) return "-";
  return new Date(iso).toLocaleString();
}

export default function Logs() {
  const [logs, setLogs] = useState([]);
  const [count, setCount] = useState(0);
  const [decision, setDecision] = useState("");
  const [provider, setProvider] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { limit: 50, offset: 0 };
      if (decision) params.decision = decision;
      if (provider) params.provider = provider;
      const data = await fetchLogs(params);
      setLogs(data.logs);
      setCount(data.count);
    } catch (err) {
      setError(err.message);
      setLogs([]);
      setCount(0);
    } finally {
      setLoading(false);
    }
  }, [decision, provider]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="stack">
      <header className="page-header">
        <h2>Request logs</h2>
        <p>One row per LLM call — prompt, provider, pass/fail, latency.</p>
      </header>

      <section className="card">
        <div className="toolbar">
          <label className="field-inline">
            <span>Decision</span>
            <select value={decision} onChange={(e) => setDecision(e.target.value)}>
              <option value="">All</option>
              <option value="pass">pass</option>
              <option value="fail">fail</option>
              <option value="block">block</option>
              <option value="warn">warn</option>
            </select>
          </label>
          <label className="field-inline">
            <span>Provider</span>
            <select value={provider} onChange={(e) => setProvider(e.target.value)}>
              <option value="">All</option>
              <option value="mock">mock</option>
              <option value="gemini">gemini</option>
              <option value="openai">openai</option>
              <option value="groq">groq</option>
            </select>
          </label>
          <button type="button" className="btn btn-secondary btn-sm" onClick={load}>
            Refresh
          </button>
          <span className="toolbar-meta">{count} total</span>
        </div>

        {loading && <p className="status-text">Loading logs...</p>}
        {error && <div className="alert alert-error">{error}</div>}

        {!loading && !error && logs.length === 0 && (
          <p className="status-text">No requests logged yet. Run an eval first.</p>
        )}

        {logs.length > 0 && (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Prompt</th>
                  <th className="col-narrow">Provider</th>
                  <th className="col-narrow">Decision</th>
                  <th>Rule hits</th>
                  <th className="col-narrow">ms</th>
                  <th>Outcome</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((row) => (
                  <tr
                    key={row.request_id}
                    className={row.decision === "fail" || row.decision === "block" ? "row-fail" : ""}
                  >
                    <td className="col-narrow mono">{formatTime(row.created_at)}</td>
                    <td className="cell-clip" title={row.prompt_excerpt}>
                      {row.prompt_excerpt}
                    </td>
                    <td className="col-narrow">{row.provider}</td>
                    <td className="col-narrow">
                      <span className={row.decision === "pass" ? "result-pass" : "result-fail"}>
                        {row.decision}
                      </span>
                    </td>
                    <td className="cell-clip mono" title={row.rule_hits.join(", ")}>
                      {row.rule_hits.join(", ") || "-"}
                    </td>
                    <td className="col-narrow">{row.latency_ms.toFixed(0)}</td>
                    <td className="cell-clip" title={row.final_outcome}>
                      {row.final_outcome}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}