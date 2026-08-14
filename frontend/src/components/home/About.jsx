import { Link } from "react-router-dom";
import { useLanguage } from "../../context/LanguageContext";
import { useHomeContent } from "../../data/useHomeContent";

/**
 * Agriva's about-section-2.
 *
 * Three template behaviours ride on the class names here:
 *   .text-anim  — SplitText word-by-word reveal, wired in main.js
 *   .count      — jquery.counterUp counts the number up when scrolled into view
 *   .video-popup — magnificPopup opens the linked video in a lightbox
 * counterUp reads the *text content* of .count, so the number must be rendered
 * as a bare integer with the suffix as a sibling, not baked into one string.
 */
export default function About() {
  const { t } = useLanguage();
  const { aboutContent } = useHomeContent();

  return (
    <section className="about-section-2 section-padding fix pt-0" id="about">
      <div className="left-shape">
        <img src="/assets/img/home-2/about-shape-1.png" alt="" />
      </div>
      <div className="right-shape">
        <img src="/assets/img/home-2/about-shape-2.png" alt="" />
      </div>
      <div className="maize-shape float-bob-y">
        <img src="/assets/img/home-1/maize-1.png" alt="" />
      </div>
      <div className="maize-shape-2 float-bob-y">
        <img src="/assets/img/home-1/maize-1.png" alt="" />
      </div>

      <div className="container">
        <div className="section-title-area">
          <div className="section-title">
            <span className="sub-title-2">
              <img src="/assets/img/home-2/icon/04.svg" alt="" /> {t("home.siteHeader.navAbout")}
            </span>
            <h2 className="text-anim">
              {aboutContent.headingLines[0]} <br />
              {aboutContent.headingLines[1]}
            </h2>
          </div>
          <div className="content">
            <p>{aboutContent.paragraph}</p>
            <Link to="/chat" className="link-btn-2">
              {t("home.hero.tryCropDoctor")}
            </Link>
          </div>
        </div>

        <div className="about-wrapper-2">
          <div className="count-wrap">
            {aboutContent.stats.map((stat, i) => (
              <div
                key={stat.label}
                className={`count-item-2${i === 1 ? " style-top" : ""}`}
              >
                <h2>
                  <span className="count">{stat.value}</span>
                  {stat.suffix}
                </h2>
                <p>{stat.label}</p>
              </div>
            ))}
          </div>
          <div className="trac-wrap">
            <div className="tractor-image float-bob-x">
              <img src="/assets/img/home-2/tractor.png" alt="" />
            </div>
          </div>
          <div className="paddy-image">
            <img src="/assets/img/home-2/paddy.png" alt="" />
            <a
              href="https://www.youtube.com/watch?v=Cn4G2lZ_g2I"
              className="video-btn video-popup ripple-2"
              aria-label="Play video"
            >
              <i className="fa-solid fa-play" />
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
