import { Fragment, useState } from "react";
import { useLanguage } from "../../context/LanguageContext";
import MilestoneDetail from "./MilestoneDetail";

export default function SeasonPlanTimeline({ cropName, milestones }) {
  const { t, tf } = useLanguage();
  const [activeId, setActiveId] = useState(null);
  const active = milestones.find((m) => m.id === activeId);

  return (
    <div className="season-plan">
      <div className="season-plan-header">
        <h2>{t("seasonPlanTimeline.title")}</h2>
        <span className="season-plan-subtitle">
          {tf("seasonPlanTimeline.subtitleTemplate", { cropName })}
        </span>
      </div>

      <div className="season-timeline">
        {milestones.map((m, i) => (
          <Fragment key={m.id}>
            <div className="season-milestone">
              <button
                type="button"
                className={`season-dot ${activeId === m.id ? "active" : ""} ${
                  m.adjustment ? "adjusted" : ""
                }`}
                onClick={() => setActiveId(activeId === m.id ? null : m.id)}
                aria-label={tf("seasonPlanTimeline.dotAriaTemplate", { name: m.name, date: m.date })}
              >
                {m.adjustment && <span className="season-dot-flag">!</span>}
              </button>
              <div
                className="season-milestone-date"
                title={
                  m.adjustment
                    ? tf("seasonPlanTimeline.dotTitleTemplate", { from: m.adjustment.from, date: m.date })
                    : m.date
                }
              >
                {m.adjustment ? (
                  <>
                    <s>{m.adjustment.from}</s> → {m.date}
                  </>
                ) : (
                  m.date
                )}
              </div>
              <div className="season-milestone-name">{m.name}</div>
            </div>
            {i < milestones.length - 1 && <div className="season-connector" />}
          </Fragment>
        ))}
      </div>

      {active && <MilestoneDetail milestone={active} />}
    </div>
  );
}
