import { useLanguage } from "../../context/LanguageContext";

const money = (n) => `৳${Number(n ?? 0).toLocaleString()}`;

/**
 * Describes how a figure moved, and whether that movement is good news.
 *
 * Direction alone is not enough to colour a delta: a fall in cost or in the
 * break-even yield is an improvement, while a fall in revenue or profit is
 * not. `betterWhen` carries that per-metric meaning so the same helper can
 * colour all of them.
 */
function delta(current, prev, betterWhen = "higher") {
  if (prev === null || prev === undefined || current === null || current === undefined) return null;
  const diff = Number(current) - Number(prev);
  // Rounding noise on floats (ROI, break-even tons) should not render as a
  // change the farmer can't see in the displayed figure.
  if (Math.abs(diff) < 0.005) return { diff: 0, unchanged: true, tone: "flat" };
  const improved = betterWhen === "higher" ? diff > 0 : diff < 0;
  return { diff, unchanged: false, tone: improved ? "up" : "down" };
}

function DeltaChip({ info, format = money }) {
  const { t } = useLanguage();
  if (!info) return null;
  if (info.unchanged) {
    return <span className="financial-delta flat">{t("financialBreakdown.unchanged")}</span>;
  }
  const sign = info.diff > 0 ? "+" : "−";
  return (
    <span className={`financial-delta ${info.tone}`}>
      <i className={`fa-solid ${info.diff > 0 ? "fa-arrow-trend-up" : "fa-arrow-trend-down"}`} />
      {sign}
      {format(Math.abs(info.diff))}
    </span>
  );
}

/**
 * `previous` holds the figures this plan replaced. It is only set when the
 * numbers actually changed during the session — a re-plan, a "what if"
 * scenario, or a monitor-agent adjustment — never on first load. When present,
 * every figure shows what it was alongside what it is, because the whole point
 * of changing a plan is judging whether the change was worth it.
 */
export default function FinancialBreakdown({ cropName, financials, previous = null }) {
  const { t, tf } = useLanguage();
  if (!financials) return null;

  const { items, cost, revenue, profit, roi, breakEvenTons } = financials;
  const comparing = Boolean(previous);

  const prevItems = new Map((previous?.items || []).map((i) => [i.label, i.amount]));

  const costDelta = comparing ? delta(cost, previous.cost, "lower") : null;
  const revenueDelta = comparing ? delta(revenue, previous.revenue, "higher") : null;
  const profitDelta = comparing ? delta(profit, previous.profit, "higher") : null;
  const roiDelta = comparing ? delta(roi, previous.roi, "higher") : null;
  const breakEvenDelta = comparing ? delta(breakEvenTons, previous.breakEvenTons, "lower") : null;

  return (
    <div className="financial-breakdown">
      <div className="financial-header">
        <h2>{t("financialBreakdown.title")}</h2>
        <span className="financial-subtitle">{cropName}</span>
        {comparing && (
          <span className="financial-compare-badge">
            <i className="fa-solid fa-code-compare" /> {t("financialBreakdown.updatedBadge")}
          </span>
        )}
      </div>

      {comparing && <p className="financial-compare-note">{t("financialBreakdown.compareNote")}</p>}

      <div className="financial-items">
        {items.map((item) => {
          const before = prevItems.get(item.label);
          const itemDelta = comparing ? delta(item.amount, before, "lower") : null;
          return (
            <div className="financial-item" key={item.label}>
              <span>{item.label}</span>
              <span className="financial-item-values">
                {itemDelta && !itemDelta.unchanged && (
                  <span className="financial-was">{money(before)}</span>
                )}
                <span>{money(item.amount)}</span>
              </span>
            </div>
          );
        })}
      </div>

      <div className="financial-divider" />

      <div className="financial-summary-row">
        <div>
          <span className="financial-summary-label">{t("financialBreakdown.totalCost")}</span>
          <span className="financial-summary-value">{money(cost)}</span>
          {comparing && (
            <span className="financial-prev-line">
              <span className="financial-was">{money(previous.cost)}</span>
              <DeltaChip info={costDelta} />
            </span>
          )}
        </div>
        <div>
          <span className="financial-summary-label">{t("financialBreakdown.revenue")}</span>
          <span className="financial-summary-value">{money(revenue)}</span>
          {comparing && (
            <span className="financial-prev-line">
              <span className="financial-was">{money(previous.revenue)}</span>
              <DeltaChip info={revenueDelta} />
            </span>
          )}
        </div>
      </div>

      <div className="financial-summary-row highlight">
        <div>
          <span className="financial-summary-label">{t("financialBreakdown.netProfit")}</span>
          <span className="financial-summary-value profit">{money(profit)}</span>
          {comparing && (
            <span className="financial-prev-line">
              <span className="financial-was">{money(previous.profit)}</span>
              <DeltaChip info={profitDelta} />
            </span>
          )}
        </div>
        <div>
          <span className="financial-summary-label">{t("financialBreakdown.roi")}</span>
          <span className="financial-summary-value">{roi}%</span>
          {comparing && (
            <span className="financial-prev-line">
              <span className="financial-was">{previous.roi}%</span>
              <DeltaChip info={roiDelta} format={(n) => `${n.toFixed(1)}%`} />
            </span>
          )}
        </div>
        <div>
          <span className="financial-summary-label">{t("financialBreakdown.breakEven")}</span>
          <span className="financial-summary-value">
            {tf("financialBreakdown.breakEvenTemplate", { tons: breakEvenTons })}
          </span>
          {comparing && (
            <span className="financial-prev-line">
              <span className="financial-was">
                {tf("financialBreakdown.breakEvenTemplate", { tons: previous.breakEvenTons })}
              </span>
              <DeltaChip info={breakEvenDelta} format={(n) => n.toFixed(2)} />
            </span>
          )}
        </div>
      </div>

      <p className="financial-whatif-note">{t("financialBreakdown.helpNote")}</p>
    </div>
  );
}
