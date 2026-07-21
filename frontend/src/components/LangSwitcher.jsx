import { useI18n } from "../context/I18nContext.jsx";

const LABELS = { fr: "FR", ar: "ع" };

// Bascule de langue FR / AR. Chaque bouton force la langue correspondante.
export default function LangSwitcher() {
  const { lang, setLang, langues } = useI18n();
  return (
    <div className="flex gap-1">
      {langues.map((l) => (
        <button
          key={l}
          onClick={() => setLang(l)}
          className={`w-8 h-8 rounded-lg text-sm font-medium ${
            lang === l ? "bg-blue-50 text-blue-600" : "text-slate-400 hover:bg-slate-50"
          }`}
        >
          {LABELS[l] ?? l.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
