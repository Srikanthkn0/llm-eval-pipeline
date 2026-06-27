const MODEL_LABELS = {
  "gemini-2.5-flash-lite": "Gemini 2.5 Flash-Lite",
  "gemini-2.5-flash": "Gemini 2.5 Flash",
  "llama-3.1-8b-instant": "Llama 3.1 8B",
  "gpt-4o-mini": "GPT-4o mini",
  "mock-model-v1": "Mock (demo)",
};

export function formatModelName(modelId) {
  if (!modelId) return "—";
  return MODEL_LABELS[modelId] || modelId;
}