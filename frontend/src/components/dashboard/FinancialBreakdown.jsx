import { useLanguage } from "../../context/LanguageContext";

export default function FinancialBreakdown({ cropName, financials }) {
  const { t, tf } = useLanguage();
  if (!financials) return null;

  const { items, cost, revenue, profit, roi, breakEvenTons } = financials;

  return (
    <div className="financial-breakdown">
      <div className="financial-header">
        <h2>{t("financialBreakdown.title")}</h2>
        <span className="financial-subtitle">{cropName}</span>
      </div>

      <div className="financial-items">
        {items.map((item) => (
          <div className="financial-item" key={item.label}>
            <span>{item.label}</span>
            <span>৳{item.amount.toLocaleString()}</span>
          </div>
        ))}
      </div>

      <div className="financial-divider" />

      <div className="financial-summary-row">
        <div>
          <span className="financial-summary-label">{t("financialBreakdown.totalCost")}</span>
          <span className="financial-summary-value">৳{cost.toLocaleString()}</span>
        </div>
        <div>
          <span className="financial-summary-label">{t("financialBreakdown.revenue")}</span>
          <span className="financial-summary-value">৳{revenue.toLocaleString()}</span>
        </div>
      </div>

      <div className="financial-summary-row highlight">
        <div>
          <span className="financial-summary-label">{t("financialBreakdown.netProfit")}</span>
          <span className="financial-summary-value profit">৳{profit.toLocaleString()}</span>
        </div>
        <div>
          <span className="financial-summary-label">{t("financialBreakdown.roi")}</span>
          <span className="financial-summary-value">{roi}%</span>
        </div>
        <div>
          <span className="financial-summary-label">{t("financialBreakdown.breakEven")}</span>
          <span className="financial-summary-value">
            {tf("financialBreakdown.breakEvenTemplate", { tons: breakEvenTons })}
          </span>
        </div>
      </div>

      <p className="financial-whatif-note">{t("financialBreakdown.helpNote")}</p>
    </div>
  );
}
