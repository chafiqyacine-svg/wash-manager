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
  graphiques: () => request("/dashboard/graphiques"),
  apercu: (siteId) => request(`/dashboard/apercu${siteId ? `?site_id=${siteId}` : ""}`),
  washDetails: (siteId) => request(`/dashboard/wash-details${siteId ? `?site_id=${siteId}` : ""}`),
  // Multi-sites & baies
  sites: () => request("/sites"),
  bays: (statut = "all", siteId) =>
    request(`/bays?statut=${statut}${siteId ? `&site_id=${siteId}` : ""}`),
  transactions: (params = "") => request(`/transactions${params}`),
  anomalies: (params = "") => request(`/anomalies${params}`),
  resoudreAnomalie: (id) => request(`/anomalies/${id}/resoudre`, { method: "POST" }),
  employes: () => request("/employes"),
  metriquesEmploye: (id) => request(`/employes/${id}/metriques`),
  forfaits: () => request("/forfaits"),
  creerForfait: (payload) => request("/forfaits", { method: "POST", body: payload }),
  modifierForfait: (id, payload) => request(`/forfaits/${id}`, { method: "PUT", body: payload }),
  supprimerForfait: (id) => request(`/forfaits/${id}`, { method: "DELETE" }),
  // Caisse intégrée (tickets)
  tickets: (statut = "") => request(`/tickets${statut ? `?statut=${statut}` : ""}`),
  creerTicket: (payload) => request("/tickets", { method: "POST", body: payload }),
  annulerTicket: (id) => request(`/tickets/${id}/annuler`, { method: "POST" }),
  rapprocherTicket: (id, transactionId) =>
    request(`/tickets/${id}/rapprocher?transaction_id=${transactionId}`, { method: "POST" }),
  transactionsNonAppariees: () => request("/transactions?non_apparie=true"),
  // Paramètres configurables
  parametres: () => request("/parametres"),
  modifierParametre: (cle, valeur) =>
    request(`/parametres/${cle}`, { method: "PUT", body: { valeur } }),
  vehicules: (plaque = "") => request(`/vehicules${plaque ? `?plaque=${plaque}` : ""}`),
  rapports: () => request("/rapports"),
};
