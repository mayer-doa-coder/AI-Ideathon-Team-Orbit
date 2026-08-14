import { createContext, useContext, useEffect, useState } from "react";
import { getStoredLanguage, setStoredLanguage, tf, translate } from "../i18n/translations";

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(getStoredLanguage);

  useEffect(() => {
    setStoredLanguage(language);
    document.documentElement.lang = language;
  }, [language]);

  function setLanguage(lang) {
    setLanguageState(lang === "bn" ? "bn" : "en");
  }

  function toggleLanguage() {
    setLanguageState((prev) => (prev === "en" ? "bn" : "en"));
  }

  const value = {
    language,
    setLanguage,
    toggleLanguage,
    t: (key) => translate(key, language),
    tf: (key, vars) => tf(key, vars, language),
  };

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within a LanguageProvider");
  return ctx;
}
