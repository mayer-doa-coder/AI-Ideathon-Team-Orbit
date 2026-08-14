import Counter from "../common/Counter";
import { useLanguage } from "../../context/LanguageContext";
import { useHomeContent } from "../../data/useHomeContent";

export default function About() {
  const { t } = useLanguage();
  const { aboutContent } = useHomeContent();
  return (
    <section className="about-section" id="about">
      <div className="section-inner">
        <div className="section-title">
          <span className="sub-title">
            <i className="fa-solid fa-leaf" /> {t("home.about.subTitle")}
          </span>
          <h2>
            {aboutContent.headingLines.map((line, i) => (
              <span key={i}>
                {line}
                {i < aboutContent.headingLines.length - 1 && <br />}
              </span>
            ))}
          </h2>
        </div>

        <div className="about-body">
          <p>{aboutContent.paragraph}</p>

          <div className="about-visual">
            <div className="about-visual-block small">
              <i className="fa-solid fa-tractor" />
            </div>
            <div className="about-visual-block large">
              <i className="fa-solid fa-satellite-dish" />
              <button type="button" className="video-btn" aria-label={t("home.about.watchDemo")}>
                <i className="fa-solid fa-play" />
              </button>
            </div>
          </div>

          <div className="about-stats">
            {aboutContent.stats.map((s) => (
              <div className="about-stat" key={s.label}>
                <h2>
                  <Counter value={s.value} suffix={s.suffix} />
                </h2>
                <p>{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
