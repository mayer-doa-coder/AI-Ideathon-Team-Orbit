import { useState } from "react";
import { useLanguage } from "../../context/LanguageContext";

const VERDICT_KEY = { SELL_NOW: "sellNow", STORE: "store", WAIT: "wait" };

export default function CropCard({ crop, isSelected, onSelect }) {
  const { t } = useLanguage();
  const [showWhy, setShowWhy] = useState(false);

  return (
    <div className={`crop-card ${isSelected ? "selected" : ""}`}>
      <div className="crop-card-header">
        <h3>{crop.name}</h3>
      </div>

      <dl className="crop-card-stats">
        <div>
          <dt>{t("cropCard.suitability")}</dt>
          <dd className={`badge badge-${crop.suitability.toLowerCase()}`}>{crop.suitability}</dd>
        </div>
        <div>
          <dt>{t("cropCard.water")}</dt>
          <dd>{crop.water}</dd>
        </div>
        <div>
          <dt>{t("cropCard.risk")}</dt>
          <dd className={`badge badge-${crop.risk.toLowerCase()}`}>{crop.risk}</dd>
        </div>
        <div>
          <dt>{t("cropCard.profit")}</dt>
          <dd className="crop-card-profit">৳{crop.profit.toLocaleString()}</dd>
        </div>
      </dl>

      <button type="button" className="crop-card-why-toggle" onClick={() => setShowWhy((v) => !v)}>
        {t("cropCard.why")} {showWhy ? "▾" : "▸"}
      </button>

      {showWhy && (
        <div className="crop-card-why">
          <p>{crop.why.knowledge}</p>
          <p>{crop.why.weather}</p>
          {crop.market && <p>{crop.market.reasons?.[0]}</p>}
        </div>
      )}

      {crop.market && (
        <div className="crop-card-market">
          <span className="crop-card-market-price">
            ৳{crop.market.current_price?.toFixed(0)}/{crop.market.unit}
          </span>
          {crop.market.verdict && (
            <span className={`market-verdict-badge market-verdict-${crop.market.verdict.toLowerCase().replace("_now", "")}`}>
              {VERDICT_KEY[crop.market.verdict] ? t(`marketPriceCard.${VERDICT_KEY[crop.market.verdict]}`) : crop.market.verdict.replace("_", " ")}
            </span>
          )}
        </div>
      )}

      <button
        type="button"
        className={`crop-card-select ${isSelected ? "selected" : ""}`}
        onClick={() => onSelect(crop)}
      >
        {isSelected ? t("cropCard.selected") : t("cropCard.select")}
      </button>
    </div>
  );
}
