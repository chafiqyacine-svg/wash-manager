# Internationalisation (FR / AR)

Infrastructure multilingue avec bascule **RTL** pour l'arabe.

## Architecture

- `fr.js`, `ar.js` — dictionnaires `clé → texte`. **Mêmes clés dans les deux.**
- `context/I18nContext.jsx` — fournit `useI18n()` → `{ t, lang, setLang, dir, langues }`.
  - `t("ma.cle")` renvoie la traduction (repli FR puis clé brute si absente).
  - Persiste la langue en `localStorage` et applique `dir`/`lang` sur `<html>`
    (l'arabe bascule toute la page en droite-à-gauche).
- `components/LangSwitcher.jsx` — boutons FR / ع (dans la barre latérale).

## Ajouter une traduction dans une page

```jsx
import { useI18n } from "../context/I18nContext.jsx";

export default function MaPage() {
  const { t } = useI18n();
  return <h1>{t("mapage.titre")}</h1>;
}
```

Puis ajouter `"mapage.titre"` dans **`fr.js` et `ar.js`**.

## TODO(dev) — pages restantes

Le menu, l'Inventaire et les Marges sont traduits (modèle de référence).
Les autres pages (`Dashboard`, `Queue`, `Bays`, `Anomalies`, `Reports`, `Config`…)
ont encore des chaînes FR en dur : les remplacer par `t("…")` en suivant le
même schéma et compléter les deux dictionnaires. Aucune logique à changer.

## RTL — points d'attention

`dir="rtl"` inverse automatiquement l'ordre des colonnes flex (la barre
latérale passe à droite). Vérifier les classes directionnelles explicites
(`border-r`, `pl-*`, `text-right`) qui ne se retournent pas seules : préférer
les variantes logiques (`ps-*`/`pe-*`, `text-start`/`text-end`) là où le sens
dépend de la langue.
