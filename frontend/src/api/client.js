const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function parseResponse(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail || `Request failed (${response.status})`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

export async function fetchHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  return parseResponse(response);
}

export async function fetchDatasets() {
  const response = await fetch(`${API_BASE_URL}/api/datasets`);
  return parseResponse(response);
}

export async function uploadDataset(file, name) {
  const formData = new FormData();
  formData.append("file", file);
  if (name) {
    formData.append("name", name);
  }

  const response = await fetch(`${API_BASE_URL}/api/datasets/upload`, {
    method: "POST",
    body: formData,
  });
  return parseResponse(response);
}

export async function runEval(payload) {
  const response = await fetch(`${API_BASE_URL}/api/evals/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
}

export async function fetchEvalRuns() {
  const response = await fetch(`${API_BASE_URL}/api/evals/runs`);
  return parseResponse(response);
}

export async function fetchEvalRun(runId) {
  const response = await fetch(`${API_BASE_URL}/api/evals/runs/${runId}`);
  return parseResponse(response);
}
