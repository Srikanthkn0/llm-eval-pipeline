import { useEffect, useState } from "react";
import {
  fetchDatasets,
  fetchEvalRun,
  fetchModels,
  startEvalJob,
  waitForEvalJob,
} from "../api/client.js";
import EvalResultsTable from "../components/EvalResultsTable.jsx";
import RunSummary from "../components/RunSummary.jsx";

const DEFAULT_PROMPT =
  "Answer the question briefly.\n\nQuestion: {input}\nAnswer:";

export default function RunEval({ onRunComplete, onNavigate }) {
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
          Each test case is sent to the selected model, scored against the expected
          output, and saved as a run you can compare over time.
        </p>

        {loading && <p className="status-text">Loading datasets and models...</p>}

        {!loading && datasets.length === 0 && (
          <div className="empty-state">
            <p>No datasets yet.</p>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => onNavigate?.("datasets")}
            >
              Upload a dataset
            </button>
          </div>
        )}

        {!loading && models.length === 0 && (
          <div className="alert alert-warn">
            No models available. Add <code>GEMINI_API_KEY</code> on the Render backend.
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
              <span className="field-hint">Use {"{input}"} where each test case should go.</span>
            </label>

            <label className="field">
              <span>Model</span>
              <select
                value={modelName}
                onChange={(event) => setModelName(event.target.value)}
              >
                {models.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.label}
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
          <RunSummary run={result} />
          <EvalResultsTable results={result.results} />
        </section>
      )}
    </div>
  );
}