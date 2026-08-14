import { Link } from "react-router-dom";
import { useLanguage } from "../../context/LanguageContext";
import { useHomeContent } from "../../data/useHomeContent";

/**
 * The fixed page furniture Agriva renders before #smooth-wrapper: back-to-top
 * button, the custom cursor pair, the offcanvas drawer and the search popup.
 *
 * All behaviour lives in assets/js/main.js — the #back-top click, the
 * .sidebar__toggle / .offcanvas__close pair, the cursor's mousemove tracking
 * and the .search_btn toggle are all bound there. These components only supply
 * the markup and class names main.js queries for, so the class names are not
 * cosmetic and must not be renamed.
 *
 * The .mobile-menu div is intentionally left empty: meanmenu clones #mobile-menu
 * from the header into it at runtime.
 */
export function BackToTop() {
  return (
    <button id="back-top" className="back-to-top theme-bg-2" aria-label="Back to top">
      <i className="fa-regular fa-arrow-up" />
    </button>
  );
}

export function MouseCursor() {
  return (
    <>
      <div className="mouseCursor cursor-outer" />
      <div className="mouseCursor cursor-inner" />
    </>
  );
}

export function Offcanvas() {
  const { t } = useLanguage();
  const { contactInfo, socialLinks } = useHomeContent();

  return (
    <>
      <div className="fix-area">
        <div className="offcanvas__info">
          <div className="offcanvas__wrapper">
            <div className="offcanvas__content">
              <div className="offcanvas__top mb-5 d-flex justify-content-between align-items-center">
                <div className="offcanvas__logo">
                  <Link to="/">
                    <img src="/assets/img/logo-mark.png" alt="Green Leaf AI" />
                  </Link>
                </div>
                <div className="offcanvas__close">
                  <button type="button" aria-label={t("home.siteHeader.toggleMenu")}>
                    <i className="fas fa-times" />
                  </button>
                </div>
              </div>

              <p className="text d-none d-xl-block">{contactInfo.blurb}</p>

              {/* meanmenu injects the cloned mobile nav here at runtime */}
              <div className="mobile-menu fix mb-3" />

              <div className="offcanvas__contact d-xl-block">
                <h4 className="d-xl-block">{contactInfo.heading}</h4>
                <ul className="d-xl-block">
                  <li className="d-flex align-items-center">
                    <div className="offcanvas__contact-icon style-2">
                      <i className="fal fa-map-marker-alt" />
                    </div>
                    <div className="offcanvas__contact-text">
                      <a href="#footer">{contactInfo.address}</a>
                    </div>
                  </li>
                  <li className="d-flex align-items-center">
                    <div className="offcanvas__contact-icon style-2 mr-15">
                      <i className="fal fa-envelope" />
                    </div>
                    <div className="offcanvas__contact-text">
                      <a href={`mailto:${contactInfo.email}`}>{contactInfo.email}</a>
                    </div>
                  </li>
                  <li className="d-flex align-items-center">
                    <div className="offcanvas__contact-icon style-2 mr-15">
                      <i className="fal fa-clock" />
                    </div>
                    <div className="offcanvas__contact-text">
                      <a href="#footer">{contactInfo.hours}</a>
                    </div>
                  </li>
                  <li className="d-flex align-items-center">
                    <div className="offcanvas__contact-icon style-2 mr-15">
                      <i className="far fa-phone" />
                    </div>
                    <div className="offcanvas__contact-text">
                      <a href={`tel:${contactInfo.phone.replace(/\s/g, "")}`}>{contactInfo.phone}</a>
                    </div>
                  </li>
                </ul>
                <div className="social-icon d-flex align-items-center style-2">
                  {socialLinks.map((social) => (
                    <a key={social.label} href={social.href} aria-label={social.label}>
                      <i className={social.icon} />
                    </a>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="offcanvas__overlay" />
    </>
  );
}

export function SearchPopup() {
  const { t } = useLanguage();

  return (
    <>
      <div className="search_popup">
        <div className="container">
          <div className="row">
            <div className="col-xxl-12">
              <div className="search_wrapper">
                <div className="search_top d-flex align-items-center">
                  <div className="search_logo">
                    <Link to="/">
                      <img src="/assets/img/logo-mark.png" alt="Green Leaf AI" />
                    </Link>
                  </div>
                  <div className="search_close">
                    <button type="button" className="search_close_btn" aria-label="Close search">
                      <i className="fa-thin fa-times" />
                    </button>
                  </div>
                </div>
                <div className="search_form">
                  {/* Search is display-only in the template; submitting would
                      reload the SPA, so it is suppressed here. */}
                  <form onSubmit={(e) => e.preventDefault()}>
                    <div className="search_input">
                      <input
                        className="search-input-field"
                        type="text"
                        placeholder={t("home.siteHeader.searchPlaceholder")}
                      />
                      <span className="search-focus-border" />
                      <button type="submit" aria-label="Search">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path
                            d="M9.55 18.1C14.272 18.1 18.1 14.272 18.1 9.55C18.1 4.82797 14.272 1 9.55 1C4.82797 1 1 4.82797 1 9.55C1 14.272 4.82797 18.1 9.55 18.1Z"
                            stroke="currentColor"
                            strokeWidth="1.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                          <path
                            d="M19.0002 19.0002L17.2002 17.2002"
                            stroke="currentColor"
                            strokeWidth="1.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="search-popup-overlay bg-theme-2" />
    </>
  );
}
