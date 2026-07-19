// Client API REST — point de raccordement unique vers le backend.
// Le token JWT est stocké en localStorage et injecté dans chaque requête.

const BASE = "/api/v1";

function getToken() {
  return localStorage.getItem("token");
}

async function request(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth && getToken()) headers["Authorization"] = `Bearer ${getToken()}`;

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 401) {
    localStorage.removeItem("token");
    // TODO(dev): rediriger vers /login proprement (via un event/context).
  }
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.status === 204 ? null : res.json();
}

export const api = {
  // Auth — login utilise le format form-urlencoded d'OAuth2.
  async login(email, password) {
    const form = new URLSearchParams({ username: email, password });
    const res = await fetch(`${BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form,
    });
    if (!res.ok) throw new Error("Identifiants invalides");
    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    return data;
  },
  logout() {
    localStorage.removeItem("token");
  },

  // Endpoints (TODO(dev): consommer dans les pages correspondantes)
  kpi: () => request("/dashboard/kpi"),
  enCours: () => request("/dashboard/en-cours"),
  transactions: (params = "") => request(`/transactions${params}`),
  anomalies: (params = "") => request(`/anomalies${params}`),
  resoudreAnomalie: (id) => request(`/anomalies/${id}/resoudre`, { method: "POST" }),
  employes: () => request("/employes"),
  metriquesEmploye: (id) => request(`/employes/${id}/metriques`),
  forfaits: () => request("/forfaits"),
  vehicules: (plaque = "") => request(`/vehicules${plaque ? `?plaque=${plaque}` : ""}`),
  rapports: () => request("/rapports"),
};
