import { useLanguage } from "../../context/LanguageContext";

export default function KnowledgeSources({ sources }) {
  const { t } = useLanguage();
  if (sources.length === 0) return null;

  return (
    <div className="knowledge-sources">
      <span className="knowledge-sources-label">{t("knowledgeSources.groundedIn")}</span>
      <ul>
        {sources.map((source) => (
          <li key={source.label}>
            {source.url ? (
              <a href={source.url} target="_blank" rel="noopener noreferrer">
                {source.label}
              </a>
            ) : (
              source.label
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
