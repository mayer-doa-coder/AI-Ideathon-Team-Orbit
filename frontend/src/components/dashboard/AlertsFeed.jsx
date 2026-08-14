import { useLanguage } from "../../context/LanguageContext";

export default function AlertsFeed({ alerts, onSimulateCheck, live = false, checking = false }) {
  const { t } = useLanguage();

  return (
    <div className="alerts-feed">
      <div className="alerts-feed-header">
        <h2>
          {t("alertsFeed.title")}
          {live && (
            <span className="live-badge" title={t("alertsFeed.liveTitle")}>
              {t("alertsFeed.live")}
            </span>
          )}
        </h2>
        <button
          type="button"
          className="alerts-simulate-btn"
          onClick={onSimulateCheck}
          disabled={checking}
        >
          {checking ? t("alertsFeed.checking") : t("alertsFeed.simulate")}
        </button>
      </div>
      <p className="alerts-feed-caption">
        {live ? t("alertsFeed.liveCaption") : t("alertsFeed.idleCaption")}
      </p>

      {alerts.length === 0 ? (
        <p className="alerts-feed-empty">{t("alertsFeed.empty")}</p>
      ) : (
        <div className="alerts-feed-list">
          {alerts.map((alert) => (
            <div className={`alert-entry alert-entry-${alert.type}`} key={alert.id}>
              <span className="alert-entry-icon">
                {alert.type === "warning" ? "!" : "OK"}
              </span>
              <span className="alert-entry-text">
                <strong>{alert.date}</strong> — {alert.text}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
