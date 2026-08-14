import { Link } from "react-router-dom";
import { useLanguage } from "../../context/LanguageContext";
import { useHomeContent } from "../../data/useHomeContent";

export default function Hero() {
  const { t } = useLanguage();
  const { heroContent } = useHomeContent();

  return (
    <section className="hero-section">
      <div className="hero-bg-pattern">
        <i className="fa-solid fa-leaf" />
        <i className="fa-solid fa-seedling" />
        <i className="fa-solid fa-wheat-awn" />
      </div>

      <div className="hero-content">
        <span className="hero-eyebrow">
          <i className="fa-solid fa-seedling" /> {heroContent.eyebrow}
        </span>
        <h1>{heroContent.heading}</h1>
        <p>{heroContent.paragraph}</p>
        <div className="hero-buttons">
          <Link to="/chat" className="theme-btn-2">
            {t("home.hero.tryCropDoctor")}
          </Link>
          <a href="#about" className="theme-btn-2 border-btn">
            {t("home.hero.seeHowItWorks")}
          </a>
        </div>
      </div>

      <div className="hero-bottom">
        <h2>{t("home.hero.whatMakesUsDifferent")}</h2>
        <div className="hero-checklist">
          {heroContent.checklist.map((item) => (
            <span key={item}>
              <i className="fa-solid fa-circle-check" /> {item}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
