import { useLanguage } from "../../context/LanguageContext";
import { useHomeContent } from "../../data/useHomeContent";

/**
 * Agriva's faq-section-2.
 *
 * The accordion is Bootstrap's, driven by the data-bs-* attributes. Bootstrap's
 * data API listens on `document`, so it keeps working on markup React mounts
 * later — no manual re-init needed. The ids must stay unique and must match
 * between the button's data-bs-target and the panel, hence the index suffix.
 *
 * The template hardcodes the two progress bars at 90%/80% in main.css. Here the
 * width is set inline from faqStats so the bar actually agrees with the number
 * printed next to it.
 */
export default function Faq() {
  const { t } = useLanguage();
  const { faqItems, faqStats } = useHomeContent();

  return (
    <section
      className="faq-section-2 section-padding fix bg-cover"
      id="faq"
      style={{ backgroundImage: "url(/assets/img/home-2/faq-bg.jpg)" }}
    >
      <div className="faq-shape float-bob-x">
        <img src="/assets/img/home-2/maize-6.png" alt="" />
      </div>

      <div className="container">
        <div className="faq-wrapper-2">
          <div className="row g-4">
            <div className="col-lg-6">
              <div className="faq-content">
                <div className="section-title mb-0">
                  <span className="sub-title-2">
                    <img src="/assets/img/home-2/icon/04.svg" alt="" /> {t("home.faq.subTitle")}
                  </span>
                  <h2 className="text-anim text-white">{t("home.faq.heading")}</h2>
                </div>

                <div className="progress-wrap">
                  {faqStats.map((stat, i) => (
                    <div className="pro-items" key={stat.title}>
                      <div className="pro-head">
                        <h3 className="title">{stat.title}</h3>
                        <span className="point">{stat.value}%</span>
                      </div>
                      <div className="progress">
                        <div
                          className={`progress-value${i === 1 ? " style-two" : ""}`}
                          style={{ width: `${stat.value}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="col-lg-6">
              <div className="faq-box">
                <div className="faq-items mt-0">
                  <div className="accordion" id="accordionExample">
                    {faqItems.map((item, i) => {
                      const isFirst = i === 0;
                      const isLast = i === faqItems.length - 1;
                      return (
                        <div
                          key={item.question}
                          className={`accordion-item${isLast ? " mb-0" : ""} wow fadeInUp`}
                          data-wow-delay={`.${(i % 3) * 2 + 3}s`}
                        >
                          <h2 className="accordion-header" id={`faqHeading${i}`}>
                            <button
                              className={`accordion-button${isFirst ? "" : " collapsed"}`}
                              type="button"
                              data-bs-toggle="collapse"
                              data-bs-target={`#faqCollapse${i}`}
                              aria-expanded={isFirst}
                              aria-controls={`faqCollapse${i}`}
                            >
                              {item.question}
                            </button>
                          </h2>
                          <div
                            id={`faqCollapse${i}`}
                            className={`accordion-collapse collapse${isFirst ? " show" : ""}`}
                            aria-labelledby={`faqHeading${i}`}
                            data-bs-parent="#accordionExample"
                            role="region"
                          >
                            <div className="accordion-body">
                              <p>{item.answer}</p>
                            </div>
                          </div>
                        </div>
                      );
                    })}
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
