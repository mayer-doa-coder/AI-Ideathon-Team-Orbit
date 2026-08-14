import { useState } from "react";
import { useLanguage } from "../../context/LanguageContext";

export default function TraceEntry({ entry }) {
  const { t } = useLanguage();
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={`trace-entry trace-entry-${entry.type}`}>
      <button
        type="button"
        className="trace-entry-header"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
      >
        <span className="trace-entry-call">
          <code>
            {entry.tool}({entry.paramsDisplay})
          </code>
          {/* Visible even collapsed, so it's provable during a demo that
              voice is a real call and not decorative — see nodes/voice_input.py
              and nodes/voice_output.py, the only two node types that set
              entry.type to these values. */}
          {(entry.type === "voice_input" || entry.type === "voice_output") && (
            <span className="trace-voice-label">
              <i className="fa-solid fa-microphone" />
              {entry.type === "voice_input" ? t("traceEntry.voiceInput") : t("traceEntry.voiceOutput")}
            </span>
          )}
        </span>
        <span className="trace-entry-chevron">{expanded ? "▾" : "▸"}</span>
      </button>

      <div className="trace-entry-summary">
        {t("traceEntry.summaryPrefix")} {entry.summary}
        {entry.badge && (
          <span className={`diagnosis-badge diagnosis-badge-${entry.badge.level}`}>{entry.badge.label}</span>
        )}
      </div>

      {expanded && (
        <div className="trace-entry-detail">
          <div className="trace-entry-detail-block">
            <span className="trace-entry-detail-label">{t("traceEntry.paramsSent")}</span>
            <pre>{JSON.stringify(entry.params, null, 2)}</pre>
          </div>
          <div className="trace-entry-detail-block">
            <span className="trace-entry-detail-label">{t("traceEntry.rawResponse")}</span>
            <pre>{JSON.stringify(entry.response, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
}
