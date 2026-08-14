import { useLanguage } from "../../context/LanguageContext";
import { useHomeContent } from "../../data/useHomeContent";

export default function Services() {
  const { t } = useLanguage();
  const { services } = useHomeContent();
  return (
    <section className="services-section" id="services">
      <div className="section-inner">
        <div className="services-grid">
          <div className="service-highlight-card">
            <span className="sub-title light">
              <i className="fa-solid fa-leaf" /> {t("home.services.subTitle")}
            </span>
            <h2>
              {t("home.services.heading1")}
              <br />
              {t("home.services.heading2")}
            </h2>
            <a href="#services" className="theme-btn-2">
              {t("home.services.viewAll")}
            </a>
          </div>

          {services.map((s) => (
            <div className="service-card" key={s.title}>
              <div className="service-card-tags">
                {s.tags.map((t) => (
                  <span key={t}>{t}</span>
                ))}
              </div>
              <p>{s.text}</p>
              <div className="service-card-image">
                <i className={s.icon} />
              </div>
              <h3>{s.title}</h3>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
