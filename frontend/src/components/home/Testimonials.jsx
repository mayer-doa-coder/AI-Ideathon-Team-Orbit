import Carousel from "../common/Carousel";
import { useLanguage } from "../../context/LanguageContext";
import { useHomeContent } from "../../data/useHomeContent";

export default function Testimonials() {
  const { t } = useLanguage();
  const { testimonials } = useHomeContent();
  return (
    <section className="testimonials-section" id="testimonials">
      <div className="section-inner">
        <div className="section-title">
          <span className="sub-title light">
            <i className="fa-solid fa-leaf" /> {t("home.testimonials.subTitle")}
          </span>
          <h2 className="light">
            {t("home.testimonials.heading1")}
            <br />
            {t("home.testimonials.heading2")}
          </h2>
        </div>

        <Carousel
          items={testimonials}
          className="testimonial-carousel"
          renderItem={(t) => (
            <div className="testimonial-card">
              <div className="testimonial-card-top">
                <span className="testimonial-avatar">{t.name.charAt(0)}</span>
                <div>
                  <h3>{t.name}</h3>
                  <span>{t.role}</span>
                </div>
              </div>
              <p>{t.quote}</p>
              <div className="testimonial-stars">
                {Array.from({ length: 5 }).map((_, i) => (
                  <i className="fa-solid fa-star" key={i} />
                ))}
              </div>
            </div>
          )}
        />
      </div>
    </section>
  );
}
