import { useEffect, useState } from "react";
import { fetchEvalRun, fetchEvalRuns, fetchModels } from "../api/client.js";
import EvalResultsTable from "../components/EvalResultsTable.jsx";
import RunSummary from "../components/RunSummary.jsx";

export default function Results({ selectedRunId, onSelectRun }) {
  const [runs, setRuns] = useState([]);
  const [detail, setDetail] = useState(null);
  const [modelLabels, setModelLabels] = useState({});
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState(null);

  async function loadRuns() {
    setLoading(true);
    setError(null);
    try {
      const [runsData, modelsData] = await Promise.all([fetchEvalRuns(), fetchModels()]);
      setRuns(runsData.runs);
      setModelLabels(
        Object.fromEntries(modelsData.models.map((model) => [model.id, model.label]))
      );
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

  function labelForModel(modelId) {
    return modelLabels[modelId] || modelId;
  }

  return (
    <div className="stack">
      <header className="page-header">
        <h2>Results</h2>
        <p>Past eval runs and per-case breakdown.</p>
      </header>

      <section className="card">
        <div className="card-header-row">
          <h3>History</h3>
          <button type="button" className="btn btn-secondary" onClick={loadRuns}>
            Refresh
          </button>
        </div>

        {loading && <p className="status-text">Loading...</p>}

        {!loading && runs.length === 0 && (
          <p className="status-text">No runs yet.</p>
        )}

        {runs.length > 0 && (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Run</th>
                  <th>Dataset</th>
                  <th>Model</th>
                  <th className="col-narrow">Pass %</th>
                  <th className="col-narrow">When</th>
                  <th className="col-narrow"></th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr key={run.run_id}>
                    <td className="mono">{run.run_id}</td>
                    <td>{run.dataset_name}</td>
                    <td>{labelForModel(run.model_name)}</td>
                    <td className="col-narrow">{(run.pass_rate * 100).toFixed(1)}</td>
                    <td className="col-narrow">
                      {new Date(run.created_at).toLocaleDateString()}
                    </td>
                    <td className="col-narrow">
                      <button
                        type="button"
                        className="btn btn-link"
                        onClick={() => loadDetail(run.run_id)}
                      >
                        open
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {error && (
          <div className="alert alert-error">
            <strong>Error.</strong> {error}
          </div>
        )}
      </section>

      {(detail || detailLoading) && (
        <section className="card">
          <h3>Detail</h3>
          {detailLoading && <p className="status-text">Loading...</p>}
          {detail && (
            <>
              <RunSummary run={detail} />
              <EvalResultsTable results={detail.results} />
            </>
          )}
        </section>
      )}
    </div>
  );
}