import { useHomeContent } from "../../data/useHomeContent";

/**
 * Agriva's feature-section-2 cards.
 *
 * tp_fade_anim + data-delay/data-fade-from are read by main.js's GSAP fade
 * setup, not by CSS — the stagger comes from the increasing data-delay values,
 * so they are generated per index rather than hardcoded.
 */
export default function Features() {
  const { features } = useHomeContent();

  return (
    <section className="feature-section-2 section-padding pb-0">
      <div className="container">
        <div className="row g-4">
          {features.map((feature, i) => (
            <div
              key={feature.title}
              className="col-xl-4 col-lg-6 col-md-6 tp_fade_anim"
              data-delay={`.${3 + i * 2}`}
              data-fade-from="left"
            >
              <div className="feature-box-item-2">
                <div className="maize-shape">
                  <img src="/assets/img/home-2/maize-5.png" alt="" />
                </div>
                <div className="masking-shape">
                  <img src="/assets/img/home-2/mask.png" alt="" />
                  <div className="masking-2">
                    <img src="/assets/img/home-2/mask-2.png" alt="" />
                  </div>
                  <div className="icon">
                    <img src={feature.icon} alt="" />
                  </div>
                </div>
                <div className="content">
                  <h3>{feature.title}</h3>
                  <p>{feature.text}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
