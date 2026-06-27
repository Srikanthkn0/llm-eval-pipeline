import { useEffect, useState } from "react";
import { fetchEvalRun, fetchEvalRuns } from "../api/client.js";
import { formatModelName } from "../utils/models.js";

export default function Results({ selectedRunId, onSelectRun }) {
  const [runs, setRuns] = useState([]);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState(null);

  async function loadRuns() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchEvalRuns();
      setRuns(data.runs);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadDetail(runId) {
    if (!runId) {
      setDetail(null);
      return;
    }

    setDetailLoading(true);
    setError(null);
    try {
      const data = await fetchEvalRun(runId);
      setDetail(data);
      onSelectRun?.(runId);
    } catch (err) {
      setError(err.message);
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  }

  useEffect(() => {
    loadRuns();
  }, []);

  useEffect(() => {
    if (selectedRunId) {
      loadDetail(selectedRunId);
    }
  }, [selectedRunId]);

  return (
    <div className="stack">
      <section className="card">
        <div className="card-header-row">
          <h2>Past runs</h2>
          <button type="button" className="btn btn-secondary" onClick={loadRuns}>
            Refresh
          </button>
        </div>

        {loading && <p className="status-text">Loading runs...</p>}

        {!loading && runs.length === 0 && (
          <p className="status-text">No eval runs saved yet.</p>
        )}

        {runs.length > 0 && (
          <table className="table">
            <thead>
              <tr>
                <th>Run ID</th>
                <th>Dataset</th>
                <th>Model</th>
                <th>Pass rate</th>
                <th>Created</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.run_id}>
                  <td className="mono">{run.run_id}</td>
                  <td>{run.dataset_name}</td>
                  <td>{formatModelName(run.model_name)}</td>
                  <td>{(run.pass_rate * 100).toFixed(1)}%</td>
                  <td>{new Date(run.created_at).toLocaleString()}</td>
                  <td>
                    <button
                      type="button"
                      className="btn btn-link"
                      onClick={() => loadDetail(run.run_id)}
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {error && (
          <div className="alert alert-error">
            <strong>Error.</strong> {error}
          </div>
        )}
      </section>

      {(detail || detailLoading) && (
        <section className="card">
          <h2>Run detail</h2>
          {detailLoading && <p className="status-text">Loading run...</p>}

          {detail && (
            <>
              <div className="metrics-grid">
                <div className="metric">
                  <span className="label">Run ID</span>
                  <span className="value mono">{detail.run_id}</span>
                </div>
                <div className="metric">
                  <span className="label">Pass rate</span>
                  <span className="value">{(detail.pass_rate * 100).toFixed(1)}%</span>
                </div>
                <div className="metric">
                  <span className="label">Passed</span>
                  <span className="value">
                    {detail.passed_cases} / {detail.total_cases}
                  </span>
                </div>
                <div className="metric">
                  <span className="label">Avg score</span>
                  <span className="value">{detail.average_score.toFixed(2)}</span>
                </div>
                <div className="metric">
                  <span className="label">Avg latency</span>
                  <span className="value">{detail.average_latency_ms.toFixed(0)} ms</span>
                </div>
              </div>

              <table className="table">
                <thead>
                  <tr>
                    <th>Input</th>
                    <th>Expected</th>
                    <th>Actual</th>
                    <th>Score</th>
                    <th>Pass</th>
                    <th>Latency</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.results.map((row, index) => (
                    <tr key={index}>
                      <td>{row.input}</td>
                      <td>{row.expected}</td>
                      <td>{row.actual}</td>
                      <td>{row.score.toFixed(2)}</td>
                      <td>
                        <span className={`badge ${row.passed ? "badge-ok" : "badge-fail"}`}>
                          {row.passed ? "pass" : "fail"}
                        </span>
                      </td>
                      <td>{row.latency_ms.toFixed(0)} ms</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </section>
      )}
    </div>
  );
}
