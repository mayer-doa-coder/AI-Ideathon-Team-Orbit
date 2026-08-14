import { useLanguage } from "../../context/LanguageContext";
import { onboardingSteps } from "../../data/dashboardScript";

export default function FarmProfileStrip({ profile }) {
  const { t } = useLanguage();

  return (
    <div className="farm-profile-strip">
      {onboardingSteps.map((step) => {
        const value = profile[step.field];
        return (
          <div key={step.field} className={`farm-profile-item ${value ? "filled" : "pending"}`}>
            <div>
              <span className="farm-profile-label">{t(`farmProfileStrip.${step.field}`)}</span>
              <span className="farm-profile-value">{value || t("farmProfileStrip.pending")}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
