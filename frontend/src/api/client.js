const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() || "http://localhost:8000";

export function getApiBaseUrl() {
  return API_BASE_URL;
}

async function parseResponse(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail || `Request failed (${response.status})`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

async function fetchWithTimeout(url, options = {}, timeoutMs = 90000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("Request timed out. The API may be waking up — retry in 30 seconds.");
    }
    throw new Error(
      `Failed to reach API at ${API_BASE_URL}. Check VITE_API_BASE_URL and that Render is running.`
    );
  } finally {
    clearTimeout(timer);
  }
}

export async function fetchHealth() {
  const response = await fetchWithTimeout(`${API_BASE_URL}/health`, {}, 45000);
  return parseResponse(response);
}

export async function fetchStats() {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/stats`);
  return parseResponse(response);
}

export async function fetchModels() {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/models`);
  return parseResponse(response);
}

export async function fetchDatasets() {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/datasets`);
  return parseResponse(response);
}

export async function uploadDataset(file, name) {
  const formData = new FormData();
  formData.append("file", file);
  if (name) {
    formData.append("name", name);
  }

  const response = await fetchWithTimeout(`${API_BASE_URL}/api/datasets/upload`, {
    method: "POST",
    body: formData,
  });
  return parseResponse(response);
}

export async function deleteDataset(name) {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/datasets/${encodeURIComponent(name)}`, {
    method: "DELETE",
  });
  return parseResponse(response);
}

export async function startEvalJob(payload) {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/evals/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
}

export async function fetchEvalJob(jobId) {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/evals/jobs/${jobId}`);
  return parseResponse(response);
}

export async function waitForEvalJob(jobId, { onProgress, intervalMs = 800 } = {}) {
  while (true) {
    const job = await fetchEvalJob(jobId);
    onProgress?.(job);

    if (job.status === "completed") {
      return job;
    }
    if (job.status === "failed") {
      throw new Error(job.error || "Evaluation job failed.");
    }

    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
}

export async function fetchEvalRuns() {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/evals/runs`);
  return parseResponse(response);
}

export async function fetchEvalRun(runId) {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/evals/runs/${runId}`);
  return parseResponse(response);
}