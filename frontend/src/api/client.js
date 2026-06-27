function resolveApiBaseUrl() {
  const configured = import.meta.env.VITE_API_BASE_URL?.trim() || "";
  const isLocalhost =
    configured.includes("localhost") || configured.includes("127.0.0.1");

  if (import.meta.env.PROD) {
    if (configured && !isLocalhost) {
      return configured;
    }
    return "";
  }

  return configured || "http://localhost:8000";
}

const API_BASE_URL = resolveApiBaseUrl();
const MAX_UPLOAD_BYTES = 2 * 1024 * 1024;

export function getApiBaseUrl() {
  if (API_BASE_URL) {
    return API_BASE_URL;
  }
  if (import.meta.env.PROD && typeof window !== "undefined") {
    return window.location.origin;
  }
  return "http://localhost:8000";
}

async function parseResponse(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail || `Request failed (${response.status})`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

async function fetchWithTimeout(url, options = {}, timeoutMs = 90000, retries = 2) {
  let lastError = null;

  for (let attempt = 0; attempt <= retries; attempt += 1) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(url, { ...options, signal: controller.signal });
      return response;
    } catch (error) {
      lastError = error;
      if (attempt < retries) {
        await new Promise((resolve) => setTimeout(resolve, 2000 * (attempt + 1)));
        continue;
      }
      if (error.name === "AbortError") {
        throw new Error(
          "Request timed out. The API may be waking up on Render's free tier — wait 30 seconds and retry."
        );
      }
      const target = API_BASE_URL || (typeof window !== "undefined" ? window.location.origin : "API");
      throw new Error(
        `Failed to reach API at ${target}. The backend may be starting up — refresh in 30 seconds.`
      );
    } finally {
      clearTimeout(timer);
    }
  }

  throw lastError;
}

export async function fetchHealth() {
  const response = await fetchWithTimeout(`${API_BASE_URL}/health`, {}, 90000, 3);
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

export async function uploadDataset(file, name, { replace = false } = {}) {
  if (file.size > MAX_UPLOAD_BYTES) {
    throw new Error("CSV must be 2 MB or smaller.");
  }

  const formData = new FormData();
  formData.append("file", file);
  if (name) {
    formData.append("name", name);
  }
  if (replace) {
    formData.append("replace", "true");
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

export async function waitForEvalJob(
  jobId,
  { onProgress, intervalMs = 800, timeoutMs = 15 * 60 * 1000 } = {}
) {
  const started = Date.now();

  while (true) {
    if (Date.now() - started > timeoutMs) {
      throw new Error(
        "Evaluation timed out after 15 minutes. Check Results for partial progress or retry."
      );
    }

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