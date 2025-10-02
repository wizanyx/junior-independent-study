const API_BASE = import.meta.env.VITE_API_BASE_URL;

export async function fetchMetrics(params: URLSearchParams) {
  const res = await fetch(`${API_BASE}/metrics?${params.toString()}`);
  if (!res.ok) throw new Error(`Metrics error: ${res.status}`);
  return res.json();
}
