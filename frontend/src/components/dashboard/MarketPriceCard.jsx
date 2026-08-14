import { useEffect, useState } from "react";
import { useLanguage } from "../../context/LanguageContext";
import { getMarketDecision, getMarketHistory } from "../../services/marketApi";

const VERDICT_KEY = { SELL_NOW: "sellNow", STORE: "store", WAIT: "wait" };
const VERDICT_CLASS = { SELL_NOW: "sell", STORE: "store", WAIT: "wait" };

export default function MarketPriceCard({ token, crops, season, district }) {
  const { t, tf } = useLanguage();
  const [crop, setCrop] = useState(crops[0] || "rice");
  const [data, setData] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showWhy, setShowWhy] = useState(false);

  useEffect(() => {
    if (!crop) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    setShowWhy(false);

    Promise.all([
      getMarketDecision(token, { crop, season, district }),
      getMarketHistory(token, { crop, season, district }),
    ])
      .then(([decisionData, historyData]) => {
        if (cancelled) return;
        setData(decisionData);
        setHistory(historyData);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [token, crop, season, district]);

  const snapshot = data?.snapshot;
  const decision = data?.decision;
  const maxPrice = Math.max(...history.map((h) => h.avg_price), 1);

  return (
    <div className="market-price-card">
      <div className="market-price-header">
        <h2>{t("marketPriceCard.title")}</h2>
        <select value={crop} onChange={(e) => setCrop(e.target.value)} className="market-crop-select">
          {crops.map((c) => (
            <option key={c} value={c}>
              {c.charAt(0).toUpperCase() + c.slice(1)}
            </option>
          ))}
        </select>
      </div>

      {loading && <p className="market-price-status">{t("marketPriceCard.loading")}</p>}
      {error && <p className="market-price-status market-price-error">{error}</p>}

      {!loading && !error && snapshot && !snapshot.has_data && (
        <p className="market-price-status">{snapshot.unavailable_reason}</p>
      )}

      {!loading && !error && snapshot?.has_data && (
        <>
          <div className="market-price-main">
            <div>
              <span className="market-price-current">৳{snapshot.current_price.toFixed(0)}</span>
              <span className="market-price-unit">/{snapshot.unit}</span>
            </div>
            {decision?.verdict && (
              <span className={`market-verdict-badge market-verdict-${VERDICT_CLASS[decision.verdict]}`}>
                {t(`marketPriceCard.${VERDICT_KEY[decision.verdict]}`) || decision.verdict}
              </span>
            )}
          </div>
          <div className="market-price-meta">
            {tf("marketPriceCard.metaTemplate", {
              district: snapshot.district_matched ? snapshot.district : t("marketPriceCard.national"),
              date: snapshot.current_price_date,
            })}
            {season && tf("marketPriceCard.metaSeasonSuffix", { season })}
          </div>

          {history.length > 1 && (
            <div className="market-price-chart">
              {history.map((h, i) => (
                <div
                  key={i}
                  className="market-price-bar"
                  style={{ height: `${Math.max((h.avg_price / maxPrice) * 100, 8)}%` }}
                  title={tf("marketPriceCard.barTitleTemplate", {
                    date: h.price_date,
                    price: h.avg_price.toFixed(0),
                    unit: h.unit,
                  })}
                />
              ))}
            </div>
          )}

          <dl className="market-price-stats">
            <div>
              <dt>{t("marketPriceCard.historicalAvg")}</dt>
              <dd>৳{snapshot.historical_average?.toFixed(0) ?? "—"}</dd>
            </div>
            <div>
              <dt>{t("marketPriceCard.change7d")}</dt>
              <dd>
                {snapshot.change_7d_pct != null
                  ? `${snapshot.change_7d_pct.toFixed(1)}%`
                  : t("marketPriceCard.insufficientData")}
              </dd>
            </div>
            <div>
              <dt>{t("marketPriceCard.change30d")}</dt>
              <dd>
                {snapshot.change_30d_pct != null
                  ? `${snapshot.change_30d_pct.toFixed(1)}%`
                  : t("marketPriceCard.insufficientData")}
              </dd>
            </div>
          </dl>

          {decision?.reasons?.length > 0 && (
            <>
              <button type="button" className="crop-card-why-toggle" onClick={() => setShowWhy((v) => !v)}>
                {t("marketPriceCard.why")} {showWhy ? "▾" : "▸"}
              </button>
              {showWhy && (
                <div className="crop-card-why">
                  {decision.reasons.map((r, i) => (
                    <p key={i}>• {r}</p>
                  ))}
                </div>
              )}
            </>
          )}

          <div className="market-price-source">{tf("marketPriceCard.sourceTemplate", { source: snapshot.source })}</div>
        </>
      )}
    </div>
  );
}
