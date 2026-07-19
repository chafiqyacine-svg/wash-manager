# Frontend — Dashboard React + Tailwind (PWA)

Interface de supervision : temps réel, KPI, historique, anomalies, employés,
rapports, configuration. Conçue comme une **PWA** (installable sur mobile sans
passer par un store, notifications push pour les alertes critiques).

## Stack

- **React + Vite** (build rapide)
- **Tailwind CSS** (mise en page responsive)
- **Recharts** (graphiques) — cf. section 10.3
- **React Router** (navigation)
- Auth **JWT** (token stocké côté client, injecté par le client API)

## Structure

```
src/
├── main.jsx            # bootstrap React + Router
├── App.jsx             # layout + routes protégées
├── api/client.js       # client REST (fetch + JWT) — point de raccordement API
├── context/AuthContext.jsx
├── components/         # Sidebar, KpiCard, ChartCard, ...
└── pages/
    ├── Login.jsx
    ├── Dashboard.jsx   # KPI + vue temps réel
    ├── LiveView.jsx    # flux caméras + overlay
    ├── History.jsx     # recherche transactions
    ├── Anomalies.jsx
    ├── Employees.jsx
    ├── Reports.jsx
    └── Config.jsx      # forfaits, seuils, zones
```

## Points à finir (`TODO(dev)`)

- Câbler chaque page aux endpoints (les URLs sont dans `api/client.js`).
- Brancher le WebSocket `/api/v1/ws/live` pour le temps réel.
- Intégrer le flux vidéo (HLS/WebRTC) dans `LiveView`.
- Compléter le `service worker` PWA (manifest présent) + notifications push.

## Démarrage

```bash
npm install
npm run dev        # http://localhost:5173
```
