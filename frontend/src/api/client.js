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
  creerSite: (payload) => request("/sites", { method: "POST", body: payload }),
  bays: (statut = "all", siteId) =>
    request(`/bays?statut=${statut}${siteId ? `&site_id=${siteId}` : ""}`),
  creerBay: (payload) => request("/bays", { method: "POST", body: payload }),
  modifierBay: (id, payload) => request(`/bays/${id}`, { method: "PATCH", body: payload }),
  // Paiements
  payments: (siteId) => request(`/payments${siteId ? `?site_id=${siteId}` : ""}`),
  // Inventaire
  produits: (siteId, sousSeuil) =>
    request(`/produits?${siteId ? `site_id=${siteId}&` : ""}${sousSeuil ? "sous_seuil=true" : ""}`),
  creerProduit: (payload) => request("/produits", { method: "POST", body: payload }),
  modifierProduit: (id, payload) => request(`/produits/${id}`, { method: "PATCH", body: payload }),
  mouvementProduit: (id, delta) =>
    request(`/produits/${id}/mouvement?delta=${delta}`, { method: "POST" }),
  supprimerProduit: (id) => request(`/produits/${id}`, { method: "DELETE" }),
  // Queue Management (mode manuel sans caméras)
  queue: (siteId) => request(`/queue${siteId ? `?site_id=${siteId}` : ""}`),
  demarrerLavage: (ticketId, bayId) =>
    request(`/queue/demarrer?ticket_id=${ticketId}&bay_id=${bayId}`, { method: "POST" }),
  terminerLavage: (transactionId) =>
    request(`/queue/terminer?transaction_id=${transactionId}`, { method: "POST" }),
  transactions: (params = "") => request(`/transactions${params}`),
  anomalies: (params = "") => request(`/anomalies${params}`),
  resoudreAnomalie: (id) => request(`/anomalies/${id}/resoudre`, { method: "POST" }),
  employes: (siteId) => request(`/employes${siteId ? `?site_id=${siteId}` : ""}`),
  creerEmploye: (payload) => request("/employes", { method: "POST", body: payload }),
  modifierEmploye: (id, payload) => request(`/employes/${id}`, { method: "PATCH", body: payload }),
  employePerformance: (jours = 7, siteId) =>
    request(`/employes/performance?jours=${jours}${siteId ? `&site_id=${siteId}` : ""}`),
  presence: (jour, siteId) =>
    request(`/employes/presence?${jour ? `jour=${jour}` : ""}${siteId ? `&site_id=${siteId}` : ""}`),
  // Pointage (selfie horodaté par le serveur)
  pointages: () => request("/pointage"),
  async pointer(employeId, type, blob) {
    const form = new FormData();
    form.append("employe_id", employeId);
    form.append("type", type);
    form.append("selfie", blob, "selfie.jpg");
    const headers = {};
    const t = localStorage.getItem("token");
    if (t) headers["Authorization"] = `Bearer ${t}`;
    const res = await fetch(`${BASE}/pointage`, { method: "POST", headers, body: form });
    if (!res.ok) throw new Error(`API ${res.status}`);
    return res.json();
  },
  // Horaires (ouverture site + travail employé)
  horairesSite: (siteId) => request(`/sites/${siteId}/horaires`),
  majHorairesSite: (siteId, horaires) =>
    request(`/sites/${siteId}/horaires`, { method: "PUT", body: horaires }),
  horairesEmploye: (empId) => request(`/employes/${empId}/horaires`),
  majHorairesEmploye: (empId, horaires) =>
    request(`/employes/${empId}/horaires`, { method: "PUT", body: horaires }),
  // Profil & utilisateurs (admin)
  me: () => request("/auth/me"),
  users: () => request("/users"),
  creerUser: (payload) => request("/users", { method: "POST", body: payload }),
  modifierUser: (id, payload) => request(`/users/${id}`, { method: "PATCH", body: payload }),
  forfaits: () => request("/forfaits"),
  creerForfait: (payload) => request("/forfaits", { method: "POST", body: payload }),
  modifierForfait: (id, payload) => request(`/forfaits/${id}`, { method: "PUT", body: payload }),
  consommation: (forfaitId) => request(`/forfaits/${forfaitId}/consommation`),
  majConsommation: (forfaitId, items) =>
    request(`/forfaits/${forfaitId}/consommation`, { method: "PUT", body: items }),
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
