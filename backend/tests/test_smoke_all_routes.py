"""Smoke test : aucune route GET sans paramètre de chemin ne renvoie 5xx.

Filet de sécurité global : parcourt le schéma OpenAPI et appelle chaque route
GET sans paramètre de chemin, pour vérifier qu'aucune ne casse (500).
Complète les tests ciblés.
"""
from datetime import date

import pytest

from app.main import app

# Paramètres de requête requis par certaines routes (sinon 422 légitime).
PARAMS = {
    "/api/v1/cloture/apercu": {"jour": date.today().isoformat()},
}


def _routes_get_sans_param():
    paths = app.openapi()["paths"]
    return sorted(
        p for p, item in paths.items()
        if "get" in item and "{" not in p and p.startswith("/api/v1")
    )


@pytest.mark.parametrize("path", _routes_get_sans_param())
def test_get_route_ne_casse_pas(client, ref, path):
    r = client.get(path, params=PARAMS.get(path, {}))
    assert r.status_code < 500, f"{path} -> {r.status_code}: {r.text[:200]}"
    # Sans paramètre requis fourni ici, on n'attend jamais de 422 non anticipé.
    assert r.status_code != 422 or path in PARAMS, f"{path} exige un paramètre non prévu"
