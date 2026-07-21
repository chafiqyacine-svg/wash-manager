import { createContext, useContext, useEffect, useMemo, useState } from "react";
import ar from "../i18n/ar.js";
import fr from "../i18n/fr.js";

// Internationalisation FR / AR avec bascule RTL pour l'arabe.
// La langue est persistée en localStorage et applique `dir`/`lang` au <html>.
const DICTS = { fr, ar };
const RTL = new Set(["ar"]);

const I18nContext = createContext(null);

export function I18nProvider({ children }) {
  const [lang, setLang] = useState(() => localStorage.getItem("lang") || "fr");
  const dir = RTL.has(lang) ? "rtl" : "ltr";

  useEffect(() => {
    localStorage.setItem("lang", lang);
    document.documentElement.lang = lang;
    document.documentElement.dir = dir;
  }, [lang, dir]);

  const value = useMemo(() => {
    const dict = DICTS[lang] || DICTS.fr;
    // t(clé) → traduction ; repli sur le FR puis sur la clé brute si absente.
    const t = (cle) => dict[cle] ?? DICTS.fr[cle] ?? cle;
    return { lang, setLang, dir, t, langues: Object.keys(DICTS) };
  }, [lang, dir]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n doit être utilisé dans <I18nProvider>");
  return ctx;
}
