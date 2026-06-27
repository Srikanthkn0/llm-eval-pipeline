import { useEffect, useState } from "react";
import { fetchDatasets, uploadDataset } from "../api/client.js";

export default function Datasets() {
  const [datasets, setDatasets] = useState([]);
  const [file, setFile] = useState(null);
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  async function loadDatasets() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDatasets();
      setDatasets(data.datasets);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDatasets();
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!file) {
      setError("Choose a CSV file first.");
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await uploadDataset(file, name.trim() || undefined);
      setSuccess(result.message);
      setFile(null);
      setName("");
      event.target.reset();
      await loadDatasets();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="stack">
      <section className="card">
        <h2>Upload dataset</h2>
        <p className="card-description">
          CSV needs columns <code>input</code> and <code>expected_output</code>.
          Optional column: <code>category</code>.
        </p>

        <form className="form" onSubmit={handleSubmit}>
          <label className="field">
            <span>CSV file</span>
            <input
              type="file"
              accept=".csv"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
            />
          </label>

          <label className="field">
            <span>Dataset name (optional)</span>
            <input
              type="text"
              placeholder="defaults to filename"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </label>

          <button type="submit" className="btn btn-primary" disabled={uploading}>
            {uploading ? "Uploading..." : "Upload"}
          </button>
        </form>

        {error && (
          <div className="alert alert-error">
            <strong>Upload failed.</strong> {error}
          </div>
        )}
        {success && (
          <div className="alert alert-success">
            {success}
          </div>
        )}
      </section>

      <section className="card">
        <h2>Saved datasets</h2>
        {loading && <p className="status-text">Loading...</p>}

        {!loading && datasets.length === 0 && (
          <p className="status-text">
            No datasets yet. Upload{" "}
            <code>backend/sample_data/sample_eval.csv</code> to get started.
          </p>
        )}

        {datasets.length > 0 && (
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>File</th>
                <th>Rows</th>
              </tr>
            </thead>
            <tbody>
              {datasets.map((dataset) => (
                <tr key={dataset.name}>
                  <td>{dataset.name}</td>
                  <td>{dataset.file_name}</td>
                  <td>{dataset.row_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
