import { useEffect, useState } from "react";
import { fetchDatasets, runEval } from "../api/client.js";

const DEFAULT_PROMPT =
  "Answer the question briefly.\n\nQuestion: {input}\nAnswer:";

export default function RunEval({ onRunComplete }) {
  const [datasets, setDatasets] = useState([]);
  const [datasetName, setDatasetName] = useState("");
  const [promptTemplate, setPromptTemplate] = useState(DEFAULT_PROMPT);
  const [modelName, setModelName] = useState("mock-model-v1");
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchDatasets();
        setDatasets(data.datasets);
        if (data.datasets.length > 0) {
          setDatasetName(data.datasets[0].name);
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

    setRunning(true);
    setError(null);
    setResult(null);

    try {
      const data = await runEval({
        dataset_name: datasetName,
        prompt_template: promptTemplate,
        model_name: modelName,
      });
      setResult(data);
      onRunComplete?.(data.run_id);
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="stack">
      <section className="card">
        <h2>Run evaluation</h2>
        <p className="card-description">
          Runs every row in the dataset through the prompt template and scores
          the model output against <code>expected_output</code>.{" "}
          <code>mock-model-v1</code> is a deterministic demo model (no API key)
          used for local dev and CI. Choose <code>gpt-4o-mini</code> for real
          OpenAI inference when <code>OPENAI_API_KEY</code> is configured on
          the backend.
        </p>

        {loading && <p className="status-text">Loading datasets...</p>}

        {!loading && datasets.length === 0 && (
          <p className="status-text">Upload a dataset before running an eval.</p>
        )}

        {datasets.length > 0 && (
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
                <option value="mock-model-v1">
                  mock-model-v1 (demo model, no API key)
                </option>
                <option value="gpt-4o-mini">
                  gpt-4o-mini (OpenAI, needs OPENAI_API_KEY on backend)
                </option>
              </select>
            </label>

            <button type="submit" className="btn btn-primary" disabled={running}>
              {running ? "Running..." : "Run eval"}
            </button>
          </form>
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
