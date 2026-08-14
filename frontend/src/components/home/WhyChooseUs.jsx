import { useLanguage } from "../../context/LanguageContext";
import { useHomeContent } from "../../data/useHomeContent";

export default function WhyChooseUs() {
  const { t } = useLanguage();
  const { whyChooseUs } = useHomeContent();
  return (
    <section className="why-choose-section" id="why-choose-us">
      <div className="section-inner why-choose-grid">
        <div className="why-choose-image">
          <i className="fa-solid fa-wheat-awn" />
        </div>

        <div className="why-choose-content">
          <span className="sub-title">
            <i className="fa-solid fa-leaf" /> {whyChooseUs.eyebrow}
          </span>
          <h2>
            {whyChooseUs.headingLines.map((line, i) => (
              <span key={i}>
                {line}
                {i < whyChooseUs.headingLines.length - 1 && <br />}
              </span>
            ))}
          </h2>
          <p>{whyChooseUs.paragraph}</p>

          <div className="why-choose-highlights">
            {whyChooseUs.highlights.map((h) => (
              <div className="why-choose-highlight" key={h.title}>
                <h3>{h.title}</h3>
                <span>{h.text}</span>
              </div>
            ))}
          </div>

          <div className="why-choose-cta">
            <a href="#services" className="theme-btn">
              {t("home.whyChooseUs.exploreServices")}
            </a>
            <div className="why-choose-phone">
              <i className="fa-solid fa-phone-volume" />
              <div>
                <h4>{t("home.whyChooseUs.callUs")}</h4>
                <h5>
                  <a href={`tel:${whyChooseUs.phone}`}>{whyChooseUs.phone}</a>
                </h5>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
