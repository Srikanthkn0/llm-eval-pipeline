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
const API_KEY = import.meta.env.VITE_API_KEY?.trim() || "";
const MAX_UPLOAD_BYTES = 2 * 1024 * 1024;

function withAuthHeaders(headers = {}) {
  if (!API_KEY) return headers;
  return { ...headers, "X-API-Key": API_KEY };
}

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
      const response = await fetch(url, {
        ...options,
        headers: withAuthHeaders(options.headers),
        signal: controller.signal,
      });
      return response;
    } catch (error) {
      lastError = error;
      if (attempt < retries) {
        await new Promise((resolve) => setTimeout(resolve, 2000 * (attempt + 1)));
        continue;
      }
      if (error.name === "AbortError") {
        throw new Error("Timed out. Render may be waking up — wait 30s and retry.");
      }
      const target = API_BASE_URL || (typeof window !== "undefined" ? window.location.origin : "API");
      throw new Error(`Can't reach ${target}. Backend may be cold — retry in 30s.`);
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

export async function fetchGuardRules(scope) {
  const params = scope ? `?scope=${encodeURIComponent(scope)}` : "";
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/guard/rules${params}`);
  return parseResponse(response);
}

export async function scanGuardText(text, scope = "input") {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/guard/scan`, {
    method: "POST",
    headers: withAuthHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ text, scope }),
  });
  return parseResponse(response);
}

export async function fetchLogs({ limit = 50, offset = 0, decision, provider, runId } = {}) {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (decision) params.set("decision", decision);
  if (provider) params.set("provider", provider);
  if (runId) params.set("run_id", runId);

  const response = await fetchWithTimeout(`${API_BASE_URL}/api/logs?${params}`);
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
      throw new Error("Eval timed out after 15 min. Check Results or retry.");
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