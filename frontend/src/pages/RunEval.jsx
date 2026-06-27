import { useEffect, useState } from "react";
import {
  fetchDatasets,
  fetchEvalRun,
  fetchModels,
  startEvalJob,
  waitForEvalJob,
} from "../api/client.js";

const DEFAULT_PROMPT =
  "Answer the question briefly.\n\nQuestion: {input}\nAnswer:";

export default function RunEval({ onRunComplete }) {
  const [datasets, setDatasets] = useState([]);
  const [models, setModels] = useState([]);
  const [datasetName, setDatasetName] = useState("");
  const [promptTemplate, setPromptTemplate] = useState(DEFAULT_PROMPT);
  const [modelName, setModelName] = useState("");
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [job, setJob] = useState(null);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const [datasetData, modelData] = await Promise.all([
          fetchDatasets(),
          fetchModels(),
        ]);
        setDatasets(datasetData.datasets);
        setModels(modelData.models);
        setModelName(modelData.default_model);
        if (datasetData.datasets.length > 0) {
          setDatasetName(datasetData.datasets[0].name);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!datasetName) {
      setError("Select a dataset first.");
      return;
    }
    if (!modelName) {
      setError("Select a model first.");
      return;
    }

    setRunning(true);
    setError(null);
    setResult(null);
    setJob(null);

    try {
      const started = await startEvalJob({
        dataset_name: datasetName,
        prompt_template: promptTemplate,
        model_name: modelName,
      });
      setJob(started);

      const finished = await waitForEvalJob(started.job_id, {
        onProgress: setJob,
      });
      const run = await fetchEvalRun(finished.run_id);
      setResult(run);
      onRunComplete?.(run.run_id);
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  }

  const progressPct =
    job && job.total > 0 ? Math.round((job.progress / job.total) * 100) : 0;

  return (
    <div className="stack">
      <section className="card">
        <h2>Run evaluation</h2>
        <p className="card-description">
          Evaluations run as background jobs with live progress. Use Gemini on
          Render (Groq is blocked on many cloud servers). Mock is for local dev/CI only.
        </p>

        {loading && <p className="status-text">Loading datasets and models...</p>}

        {!loading && datasets.length === 0 && (
          <p className="status-text">Upload a dataset before running an eval.</p>
        )}

        {!loading && models.length === 0 && (
          <div className="alert alert-warn">
            No models available. Configure <code>GEMINI_API_KEY</code> on the backend.
          </div>
        )}

        {datasets.length > 0 && models.length > 0 && (
          <form className="form" onSubmit={handleSubmit}>
            <label className="field">
              <span>Dataset</span>
              <select
                value={datasetName}
                onChange={(event) => setDatasetName(event.target.value)}
              >
                {datasets.map((dataset) => (
                  <option key={dataset.name} value={dataset.name}>
                    {dataset.name} ({dataset.row_count} rows)
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Prompt template</span>
              <textarea
                rows={5}
                value={promptTemplate}
                onChange={(event) => setPromptTemplate(event.target.value)}
              />
              <span className="field-hint">Include {"{input}"} where the test case goes.</span>
            </label>

            <label className="field">
              <span>Model</span>
              <select
                value={modelName}
                onChange={(event) => setModelName(event.target.value)}
              >
                {models.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.label} ({model.provider})
                  </option>
                ))}
              </select>
            </label>

            <button type="submit" className="btn btn-primary" disabled={running}>
              {running ? "Running evaluation..." : "Run eval"}
            </button>
          </form>
        )}

        {running && job && (
          <div className="progress-block">
            <div className="progress-meta">
              <span>Status: {job.status}</span>
              <span>
                {job.progress} / {job.total || "—"} cases
              </span>
            </div>
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${progressPct}%` }} />
            </div>
          </div>
        )}

        {error && (
          <div className="alert alert-error">
            <strong>Run failed.</strong> {error}
          </div>
        )}
      </section>

      {result && (
        <section className="card">
          <h2>Run summary</h2>
          <div className="metrics-grid">
            <div className="metric">
              <span className="label">Run ID</span>
              <span className="value mono">{result.run_id}</span>
            </div>
            <div className="metric">
              <span className="label">Pass rate</span>
              <span className="value">{(result.pass_rate * 100).toFixed(1)}%</span>
            </div>
            <div className="metric">
              <span className="label">Passed</span>
              <span className="value">
                {result.passed_cases} / {result.total_cases}
              </span>
            </div>
            <div className="metric">
              <span className="label">Avg score</span>
              <span className="value">{result.average_score.toFixed(2)}</span>
            </div>
            <div className="metric">
              <span className="label">Avg latency</span>
              <span className="value">{result.average_latency_ms.toFixed(0)} ms</span>
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
              {result.results.map((row, index) => (
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
        </section>
      )}
    </div>
  );
}