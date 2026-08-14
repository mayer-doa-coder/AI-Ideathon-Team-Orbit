import { Link } from "react-router-dom";
import { useLanguage } from "../../context/LanguageContext";
import { useHomeContent } from "../../data/useHomeContent";

/**
 * Agriva's why-choose-us-section-2.
 *
 * `wow fadeInUp` + data-wow-delay is the WOW.js scroll-reveal (initialised in
 * main.js as `new WOW().init()`), and is a different system from the
 * tp_fade_anim/GSAP one used in Features — the template mixes both, so both
 * are preserved as-is rather than normalised to one.
 */
export default function WhyChooseUs() {
  const { t } = useLanguage();
  const { whyChooseUs } = useHomeContent();

  return (
    <section className="why-choose-us-section-2 section-padding fix theme-bg-2" id="why-choose-us">
      <div className="left-shape float-bob-x">
        <img src="/assets/img/home-2/maize-shape.png" alt="" />
      </div>
      <div className="right-shape float-bob-x">
        <img src="/assets/img/home-2/maize-shape-2.png" alt="" />
      </div>
      <div className="maize-3">
        <img src="/assets/img/home-1/maize-2.png" alt="" />
      </div>

      <div className="container">
        <div className="why-choose-us-wrapper-2">
          <div className="row g-4">
            <div className="col-lg-6">
              <div className="why-choose-us-image float-bob-y">
                <img src="/assets/img/home-2/maize.png" alt="" />
                <div className="circle-shape">
                  <img src="/assets/img/home-2/circle.png" alt="" />
                </div>
              </div>
            </div>

            <div className="col-lg-6">
              <div className="why-choose-us-content">
                <div className="section-title mb-0">
                  <span className="sub-title-2 style-2">
                    <img src="/assets/img/home-2/icon/05.svg" alt="" /> {whyChooseUs.eyebrow}
                  </span>
                  <h2 className="text-anim">
                    {whyChooseUs.headingLines[0]} {whyChooseUs.headingLines[1]}
                  </h2>
                </div>

                <p className="text wow fadeInUp" data-wow-delay=".3s">
                  {whyChooseUs.paragraph}
                </p>

                <div className="choose-us-box wow fadeInUp" data-wow-delay=".5s">
                  {whyChooseUs.highlights.map((highlight, i) => (
                    <div key={highlight.title} className={`content${i === 1 ? " style-2" : ""}`}>
                      <h3>{highlight.title}</h3>
                      <span>{highlight.text}</span>
                    </div>
                  ))}
                </div>

                <div className="choose-us-btn-item wow fadeInUp" data-wow-delay=".3s">
                  <Link to="/chat" className="theme-btn">
                    {t("home.hero.tryCropDoctor")}
                  </Link>
                  <div className="icon-item">
                    <div className="icon">
                      <img src="/assets/img/home-2/icon/06.svg" alt="" />
                    </div>
                    <div className="cont">
                      <h4>{t("home.siteHeader.navContact")} :</h4>
                      <h5>
                        <a href={`tel:${whyChooseUs.phone.replace(/\s/g, "")}`}>{whyChooseUs.phone}</a>
                      </h5>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
