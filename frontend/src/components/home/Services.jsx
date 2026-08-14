import { Link } from "react-router-dom";
import { useLanguage } from "../../context/LanguageContext";
import { useHomeContent } from "../../data/useHomeContent";

// The template hardcodes one photo per service card (service/02.jpg …05.jpg).
// Deriving the path by index keeps that pairing while letting the services
// list in homeContent.js grow; 01 is the section's background card and 06–08
// belong to the slider, so cards start at 02.
const cardImage = (index) => `/assets/img/home-2/service/0${(index % 4) + 2}.jpg`;

/**
 * Agriva's service-section-2.
 *
 * The grid is: one background "view all" card, then one card per service, then
 * a Swiper image slider. .service-image-slider is initialised in main.js and
 * pairs with the .swiper-dot4 pagination element below it — both must be
 * present or Swiper throws on the missing pagination target.
 */
export default function Services() {
  const { t } = useLanguage();
  const { services } = useHomeContent();

  return (
    <section className="service-section-2 section-padding fix" id="services">
      <div className="mask-image wt-about-title2">
        <img src="/assets/img/home-2/service/image.png" alt="" className="animated-img" />
      </div>

      <div className="container">
        <div className="row g-4">
          <div className="col-xl-4 col-lg-6 col-md-6 tp_fade_anim" data-delay=".3" data-fade-from="left">
            <div
              className="service-bg-item bg-cover"
              style={{ backgroundImage: "url(/assets/img/home-2/service/01.jpg)" }}
            >
              <div className="service-cont">
                <div className="section-title mb-0">
                  <span className="sub-title-2">
                    <img src="/assets/img/home-2/icon/04.svg" alt="" /> {t("home.services.subTitle")}
                  </span>
                  <h2 className="text-anim text-white">
                    {t("home.services.heading1")} <br />
                    {t("home.services.heading2")}
                  </h2>
                </div>
                <Link to="/chat" className="theme-btn-2">
                  {t("home.services.viewAll")}
                </Link>
              </div>
            </div>
          </div>

          {services.map((service, i) => (
            <div
              key={service.title}
              className="col-xl-4 col-lg-6 col-md-6 tp_fade_anim"
              data-delay={`.${((i + 1) % 3) * 2 + 3}`}
              data-fade-from="left"
            >
              <div className="service-card-items-2">
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
                <h3>
                  <Link to="/chat">{service.title}</Link>
                </h3>
              </div>
            </div>
          ))}

          <div className="col-xl-4 col-lg-6 col-md-6 tp_fade_anim" data-delay=".7" data-fade-from="left">
            <div className="service-image-item">
              <div className="swiper service-image-slider">
                <div className="swiper-wrapper">
                  {["06", "07", "08"].map((n) => (
                    <div className="swiper-slide" key={n}>
                      <div className="slider-thumb">
                        <img src={`/assets/img/home-2/service/${n}.jpg`} alt="" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="swiper-dot4">
                <div className="dot2" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
