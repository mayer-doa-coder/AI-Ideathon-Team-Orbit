import { useLanguage } from "../../context/LanguageContext";
import TraceEntry from "./TraceEntry";

export default function TraceLog({ entries }) {
  const { t } = useLanguage();

  return (
    <div className="trace-log">
      <div className="trace-log-header">
        <h2>{t("traceLog.title")}</h2>
        <span className="trace-log-count">
          {entries.length} {t("traceLog.callsSuffix")}
        </span>
      </div>

      {entries.length === 0 ? (
        <p className="trace-log-empty">{t("traceLog.empty")}</p>
      ) : (
        <div className="trace-log-list">
          {entries.map((entry) => (
            <TraceEntry key={entry.id} entry={entry} />
          ))}
        </div>
      )}
    </div>
  );
}
