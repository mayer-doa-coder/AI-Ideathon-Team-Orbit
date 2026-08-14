import { Link } from "react-router-dom";
import { useLanguage } from "../../context/LanguageContext";
import { useHomeContent } from "../../data/useHomeContent";

/**
 * Agriva's "hero-2" portfolio-revealing slider.
 *
 * main.js drives this entirely from class names (see the block around
 * hero-portfolio-revealing-slide in assets/js/main.js): it indexes the slides,
 * stamps .hero-portfolio-revealing-slide-N onto each, and moves .s-active /
 * .s-prev between them while animating the headings with SplitText. React only
 * renders the initial markup — .s-active on the first slide is the starting
 * state main.js expects, so it stays hardcoded here.
 *
 * data-background is resolved by main.js too (it copies the attribute into
 * background-image), which is why the slide images are attributes rather than
 * React style props.
 */
export default function Hero() {
  const { t } = useLanguage();
  const { heroContent } = useHomeContent();

  return (
    <section className="hero-section hero-2 fix">
      <div className="hero-portfolio-revealing-slider">
        <div className="hero-portfolio-revealing-slider-slides">
          {heroContent.slides.map((slide, i) => (
            <div
              key={slide.heading}
              className={`hero-portfolio-revealing-slide${i === 0 ? " s-active" : ""}`}
            >
              <div
                className="hero-portfolio-revealing-slide-inner bg-cover"
                data-background={slide.image}
              >
                <div className="container">
                  <div className="row justify-content-center">
                    <div className="col-lg-9">
                      <div className="hero-portfolio-revealing-slide-content">
                        <div className="icon">
                          <img src="/assets/img/home-2/icon/03.svg" alt="" />
                        </div>
                        <span>{slide.eyebrow}</span>
                        <h1 className="hero-portfolio-revealing-slide-heading">{slide.heading}</h1>
                        <p>{slide.paragraph}</p>
                        <div className="hero-button" data-animation="fadeInUp" data-delay="1.5s">
                          <Link to="/chat" className="theme-btn-2">
                            {t("home.hero.tryCropDoctor")}
                          </Link>
                          <a href="#about" className="theme-btn-2 border-btn">
                            {t("home.hero.seeHowItWorks")}
                          </a>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="hero-portfolio-revealing-slider-control">
          <img
            src="/assets/img/home-2/icon/01.svg"
            alt=""
            className="hero-portfolio-revealing-slider-control-line"
          />
        </div>
        <div className="hero-portfolio-revealing-slider-control hero-portfolio-revealing-slider-control-right m-right">
          <img
            src="/assets/img/home-2/icon/12.svg"
            alt=""
            className="hero-portfolio-revealing-slider-control-line"
          />
        </div>
      </div>

      <div className="hero-border-item">
        <div className="hero-bottom-item">
          <h2>{t("home.hero.whatMakesUsDifferent")}</h2>
          <div className="hero-list">
            {heroContent.checklist.map((item) => (
              <span key={item}>
                <i className="fa-solid fa-circle-check" /> {item}
              </span>
            ))}
          </div>
        </div>
        <div className="pagi-item">
          <div className="dot-number">
            <span className="dot-num">
              <span>02</span>
            </span>
            <span className="dot-num">
              <span className="style-2">0{heroContent.slides.length}</span>
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
