import { useLanguage } from "../../context/LanguageContext";
import { useHomeContent } from "../../data/useHomeContent";

// The template pairs its three quotes with these specific portraits; keeping
// the order preserves that pairing as the testimonials list is edited.
const PORTRAITS = [
  "/assets/img/home-1/testimonial/03.png",
  "/assets/img/home-1/testimonial/02.png",
  "/assets/img/home-1/testimonial/05.png",
];

/**
 * Agriva's testimonial-section-2.
 *
 * .testimonial-slider is a Swiper created in main.js, and its navigation is
 * bound to the .array-prev / .array-next buttons above it — those class names
 * are the Swiper config's navigation selectors, so the buttons must stay
 * inside this section and keep those exact names.
 */
export default function Testimonials() {
  const { t } = useLanguage();
  const { testimonials } = useHomeContent();

  return (
    <section
      className="testimonial-section-2 section-padding pt-0 fix bg-cover"
      id="testimonials"
      style={{ backgroundImage: "url(/assets/img/home-2/testimonial-bg.jpg)" }}
    >
      <div className="client-man">
        <img src="/assets/img/home-2/client.png" alt="" />
      </div>

      <div className="container">
        <div className="testimonial-top-item">
          <div className="section-title">
            <span className="sub-title-2">
              <img src="/assets/img/home-2/icon/04.svg" alt="" /> {t("home.testimonials.subTitle")}
            </span>
            <h2 className="text-anim">
              {t("home.testimonials.heading1")} <br />
              {t("home.testimonials.heading2")}
            </h2>
          </div>
          <div className="right-item">
            <div className="star">
              <img src="/assets/img/home-2/star.png" alt="" />
            </div>
            <div className="arrow-button">
              <button className="array-prev" type="button" aria-label={t("home.carousel.previous")}>
                <img src="/assets/img/home-2/icon/01.svg" alt="" />
              </button>
              <button className="array-next" type="button" aria-label={t("home.carousel.next")}>
                <img src="/assets/img/home-2/icon/02.svg" alt="" />
              </button>
            </div>
          </div>
        </div>

        <div className="testimonial-wrapper-2">
          <div className="swiper testimonial-slider">
            <div className="swiper-wrapper">
              {testimonials.map((testimonial, i) => (
                <div className="swiper-slide" key={testimonial.name}>
                  <div className="testimonial-card-item-2">
                    <div className="content">
                      <div className="client-image">
                        <img src={PORTRAITS[i % PORTRAITS.length]} alt="" />
                      </div>
                      <h3>{testimonial.name}</h3>
                      <span>{testimonial.role}</span>
                    </div>
                    <p>{testimonial.quote}</p>
                    {/* The template puts a 5-star rating here. These cards
                        describe the system's data sources rather than customer
                        reviews (see the note on `testimonials` in
                        data/homeContent.js), and a star rating on Open-Meteo
                        would be meaningless. Restore this block along with the
                        stars if real farmer quotes replace the sources. */}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
