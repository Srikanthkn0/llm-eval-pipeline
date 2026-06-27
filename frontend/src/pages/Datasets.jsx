import { useEffect, useState } from "react";
import { deleteDataset, fetchDatasets, uploadDataset } from "../api/client.js";

const MAX_UPLOAD_MB = 2;

export default function Datasets() {
  const [datasets, setDatasets] = useState([]);
  const [file, setFile] = useState(null);
  const [name, setName] = useState("");
  const [replaceExisting, setReplaceExisting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState(null);
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
      const result = await uploadDataset(file, name.trim() || undefined, {
        replace: replaceExisting,
      });
      setSuccess(result.message);
      setFile(null);
      setName("");
      setReplaceExisting(false);
      event.target.reset();
      await loadDatasets();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(datasetName) {
    setDeleting(datasetName);
    setError(null);
    setSuccess(null);

    try {
      const result = await deleteDataset(datasetName);
      setSuccess(result.message);
      setConfirmDelete(null);
      await loadDatasets();
    } catch (err) {
      setError(err.message);
    } finally {
      setDeleting(null);
    }
  }

  return (
    <div className="stack">
      <header className="page-header">
        <h2>Datasets</h2>
        <p>
          CSV with <code>input</code> and <code>expected_output</code>. Optional{" "}
          <code>category</code>. Max {MAX_UPLOAD_MB} MB.
        </p>
      </header>

      <section className="card">
        <h3>Upload</h3>
        <form className="form" onSubmit={handleSubmit}>
          <label className="field">
            <span>File</span>
            <input
              type="file"
              accept=".csv"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
            />
          </label>

          <label className="field">
            <span>Name</span>
            <input
              type="text"
              placeholder="uses filename if empty"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </label>

          <label className="field field-checkbox">
            <input
              type="checkbox"
              checked={replaceExisting}
              onChange={(event) => setReplaceExisting(event.target.checked)}
            />
            <span>Overwrite if name exists</span>
          </label>

          <button type="submit" className="btn btn-primary" disabled={uploading}>
            {uploading ? "Uploading..." : "Upload"}
          </button>
        </form>

        {error && (
          <div className="alert alert-error">
            <strong>Error.</strong> {error}
          </div>
        )}
        {success && <div className="alert alert-success">{success}</div>}
      </section>

      <section className="card">
        <h3>Saved</h3>
        {loading && <p className="status-text">Loading...</p>}

        {!loading && datasets.length === 0 && (
          <p className="status-text">Nothing uploaded yet.</p>
        )}

        {datasets.length > 0 && (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>File</th>
                  <th className="col-narrow">Rows</th>
                  <th className="col-narrow"></th>
                </tr>
              </thead>
              <tbody>
                {datasets.map((dataset) => (
                  <tr key={dataset.name}>
                    <td>{dataset.name}</td>
                    <td className="mono">{dataset.file_name}</td>
                    <td className="col-narrow">{dataset.row_count}</td>
                    <td className="table-actions col-narrow">
                      {confirmDelete === dataset.name ? (
                        <span className="confirm-row">
                          <button
                            type="button"
                            className="btn btn-link btn-danger"
                            disabled={deleting === dataset.name}
                            onClick={() => handleDelete(dataset.name)}
                          >
                            {deleting === dataset.name ? "..." : "confirm"}
                          </button>
                          <button
                            type="button"
                            className="btn btn-link"
                            onClick={() => setConfirmDelete(null)}
                          >
                            cancel
                          </button>
                        </span>
                      ) : (
                        <button
                          type="button"
                          className="btn btn-link btn-danger"
                          onClick={() => setConfirmDelete(dataset.name)}
                        >
                          delete
                        </button>
                      )}
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