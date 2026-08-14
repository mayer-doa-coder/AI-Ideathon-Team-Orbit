import { useLanguage } from "../../context/LanguageContext";

export default function MilestoneDetail({ milestone }) {
  const { language, t, tf } = useLanguage();

  return (
    <div className="milestone-detail">
      <div className="milestone-detail-title">
        {tf("milestoneDetail.titleTemplate", { name: milestone.name, date: milestone.date })}
      </div>

      {milestone.adjustment && (
        <div className="milestone-adjustment">
          {/* Word order differs between languages ("Moved from X to Y" vs.
              "X থেকে সরিয়ে Y করা হয়েছে"), and <s>/<strong> styling on the
              dynamic from/to values can't survive a plain string template —
              so this one branches directly instead of going through tf(). */}
          {language === "bn" ? (
            <>
              <s>{milestone.adjustment.from}</s> থেকে সরিয়ে <strong>{milestone.adjustment.to}</strong> করা
              হয়েছে — {milestone.adjustment.reason}
            </>
          ) : (
            <>
              Moved from <s>{milestone.adjustment.from}</s> to <strong>{milestone.adjustment.to}</strong> —{" "}
              {milestone.adjustment.reason}
            </>
          )}
        </div>
      )}

      <div className="milestone-detail-rows">
        <div>
          <span className="milestone-detail-label">{t("milestoneDetail.what")}</span>
          <span>{milestone.what}</span>
        </div>
        <div>
          <span className="milestone-detail-label">{t("milestoneDetail.whyThisDate")}</span>
          <span>{milestone.why}</span>
        </div>
        {milestone.quantity && (
          <div>
            <span className="milestone-detail-label">{t("milestoneDetail.quantity")}</span>
            <span>{milestone.quantity}</span>
          </div>
        )}
        <div>
          <span className="milestone-detail-label">{t("milestoneDetail.cost")}</span>
          <span>৳{milestone.cost.toLocaleString()}</span>
        </div>
        {milestone.organicAlternative && (
          <div>
            <span className="milestone-detail-label">{t("milestoneDetail.organicAlternative")}</span>
            <span>{milestone.organicAlternative}</span>
          </div>
        )}
      </div>
    </div>
  );
}
