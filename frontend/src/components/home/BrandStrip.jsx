import { useHomeContent } from "../../data/useHomeContent";

/**
 * Agriva's brand-section-2 marquee.
 *
 * Each Swiper slide stacks two logos (.brand-box-1 with two .brand-img-1
 * spans) — the template pairs 01–07 with 08–14. brandLogos holds the first
 * seven, so the partner logo is derived by offsetting the index into the same
 * numbered set.
 */
export default function BrandStrip() {
  const { brandLogos } = useHomeContent();

  return (
    <div className="brand-section-2 section-padding pt-0 fix">
      <div className="container">
        <div className="swiper brand-slider">
          <div className="swiper-wrapper">
            {brandLogos.map((logo, i) => {
              const partner = `/assets/img/home-1/brand/${String(i + 8).padStart(2, "0")}.png`;
              return (
                <div className="swiper-slide" key={logo}>
                  <div className="brand-box-1">
                    <span className="brand-img-1">
                      <img src={logo} alt="" />
                    </span>
                    <span className="brand-img-1">
                      <img src={partner} alt="" />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
