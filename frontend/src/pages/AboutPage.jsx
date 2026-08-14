import { Link } from "react-router-dom";
import MarketingLayout from "../components/marketing/MarketingLayout";
import Breadcrumb from "../components/marketing/Breadcrumb";
import About from "../components/home/About";
import ProcessSection from "../components/home/ProcessSection";
import BrandStrip from "../components/home/BrandStrip";
import { useLanguage } from "../context/LanguageContext";
import { useHomeContent } from "../data/useHomeContent";

/**
 * /about — the problem AgriSense exists to solve, the two-agent architecture,
 * and an explicit list of what is and is not built.
 *
 * The "what is not built" table is deliberate, not an oversight: PROJECT_OVERVIEW.md
 * makes being upfront about it a stated value, and a judge who finds a
 * placeholder feature themselves trusts the rest of the page less.
 */
export default function AboutPage() {
  const { t } = useLanguage();
  const { aboutPage } = useHomeContent();

  return (
    <MarketingLayout>
      <Breadcrumb title={t("about.title")} />

      {/* The farmer's decision chain — the problem statement */}
      <section className="section-padding fix">
        <div className="container">
          <div className="row g-4 align-items-center">
            <div className="col-lg-6">
              <div className="section-title mb-0">
                <span className="sub-title-2">
                  <img src="/assets/img/home-2/icon/04.svg" alt="" /> {t("about.problemEyebrow")}
                </span>
                <h2 className="text-anim">{aboutPage.problemHeading}</h2>
              </div>
              <p className="mt-3">{aboutPage.problemIntro}</p>
              <div className="choose-us-box mt-4">
                <div className="content">
                  <h3>{aboutPage.problemListHeading}</h3>
                  <span>
                    <ul className="list-area mt-2">
                      {aboutPage.problemQuestions.map((q) => (
                        <li key={q}>
                          <i className="fa-solid fa-chevron-right" /> {q}
                        </li>
                      ))}
                    </ul>
                  </span>
                </div>
              </div>
              <p className="mt-4">{aboutPage.problemOutro}</p>
            </div>

            <div className="col-lg-6">
              <div className="why-choose-us-image">
                <img src="/assets/img/home-2/maize.png" alt="" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Reuses the home page's two-agent explainer and the process timeline */}
      <About />
      <ProcessSection />

      {/* What is built vs what is not */}
      <section className="section-padding fix theme-bg-2">
        <div className="container">
          <div className="section-title text-center">
            <span className="sub-title-2 style-2">
              <img src="/assets/img/home-2/icon/05.svg" alt="" /> {t("about.statusEyebrow")}
            </span>
            <h2 className="text-anim">{aboutPage.statusHeading}</h2>
          </div>
          <p className="text-center mx-auto" style={{ maxWidth: "760px" }}>
            {aboutPage.statusIntro}
          </p>

          <div className="row g-4 mt-2">
            <div className="col-lg-6">
              <div className="service-card-items-2 h-100">
                <div className="top-content">
                  <div className="tag-list">
                    <span>{t("about.builtTag")}</span>
                  </div>
                </div>
                <h3 className="mb-3">{t("about.builtHeading")}</h3>
                <ul className="list-area">
                  {aboutPage.built.map((item) => (
                    <li key={item}>
                      <i className="fa-solid fa-circle-check" /> {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="col-lg-6">
              <div className="service-card-items-2 h-100">
                <div className="top-content">
                  <div className="tag-list">
                    <span>{t("about.notBuiltTag")}</span>
                  </div>
                </div>
                <h3 className="mb-3">{t("about.notBuiltHeading")}</h3>
                <ul className="list-area">
                  {aboutPage.notBuilt.map((item) => (
                    <li key={item}>
                      <i className="fa-solid fa-circle-minus" /> {item}
                    </li>
                  ))}
                </ul>
                <p className="mt-3">{aboutPage.notBuiltNote}</p>
              </div>
            </div>
          </div>

          <div className="text-center mt-5">
            <Link to="/chat" className="theme-btn">
              {t("home.hero.tryCropDoctor")}
            </Link>
          </div>
        </div>
      </section>

      <BrandStrip />
    </MarketingLayout>
  );
}
