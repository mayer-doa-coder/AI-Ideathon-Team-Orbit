import { Link } from "react-router-dom";
import MarketingLayout from "../components/marketing/MarketingLayout";
import Breadcrumb from "../components/marketing/Breadcrumb";
import Faq from "../components/home/Faq";
import BrandStrip from "../components/home/BrandStrip";
import { useLanguage } from "../context/LanguageContext";
import { useHomeContent } from "../data/useHomeContent";

// Same index-derived pairing the home page's Services section uses, so a
// service keeps the same photo on both pages.
const cardImage = (index) => `/assets/img/home-2/service/0${(index % 4) + 2}.jpg`;

/**
 * /services — one detailed card per shipping capability, expanded from the
 * home page's summary list with the specific inputs, outputs and backing
 * module for each. Everything here is a Tier 0/Tier 1 item marked Done in
 * README.md; the four placeholder features are absent by design.
 */
export default function ServicesPage() {
  const { t } = useLanguage();
  const { services, serviceDetails } = useHomeContent();

  return (
    <MarketingLayout>
      <Breadcrumb title={t("services.title")} />

      <section className="service-section-2 section-padding fix">
        <div className="container">
          <div className="section-title text-center">
            <span className="sub-title-2">
              <img src="/assets/img/home-2/icon/04.svg" alt="" /> {t("home.services.subTitle")}
              <img src="/assets/img/home-2/icon/04.svg" alt="" className="ms-2" />
            </span>
            <h2 className="text-anim">{t("services.heading")}</h2>
          </div>

          <div className="row g-4">
            {services.map((service, i) => {
              const detail = serviceDetails[i] || {};
              return (
                <div
                  className="col-xl-6 col-lg-6 tp_fade_anim"
                  data-delay={`.${(i % 3) * 2 + 3}`}
                  data-fade-from={i % 2 === 0 ? "left" : "right"}
                  key={service.title}
                >
                  <div className="service-card-items-2 h-100">
                    <div className="top-content">
                      <div className="tag-list">
                        {service.tags.map((tag) => (
                          <span key={tag}>{tag}</span>
                        ))}
                      </div>
                      <p>{service.text}</p>
                    </div>
                    <div className="service-image">
                      <img src={cardImage(i)} alt="" />
                    </div>
                    <h3 className="mt-3">
                      <Link to="/chat">{service.title}</Link>
                    </h3>
                    {detail.body && <p className="mt-2">{detail.body}</p>}
                    {detail.points && (
                      <ul className="list-area mt-3">
                        {detail.points.map((point) => (
                          <li key={point}>
                            <i className="fa-solid fa-chevron-right" /> {point}
                          </li>
                        ))}
                      </ul>
                    )}
                    {detail.meta && (
                      <span className="agri-flow-meta mt-3">
                        <i className="fa-solid fa-bolt" />
                        {detail.meta}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="text-center mt-5">
            <Link to="/chat" className="theme-btn">
              {t("home.hero.tryCropDoctor")}
            </Link>
          </div>
        </div>
      </section>

      <Faq />
      <BrandStrip />
    </MarketingLayout>
  );
}
