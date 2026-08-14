import { useLanguage } from "../context/LanguageContext";
import * as en from "./homeContent";
import * as bn from "./homeContent.bn";

// Picks the whole marketing-content module by language rather than
// translating field-by-field — homeContent.js is large prose/lists, not
// short UI-chrome strings, so a parallel data file (homeContent.bn.js) is
// easier to keep correct than threading every nested array through
// i18n/translations.js.
export function useHomeContent() {
  const { language } = useLanguage();
  return language === "bn" ? bn : en;
}
