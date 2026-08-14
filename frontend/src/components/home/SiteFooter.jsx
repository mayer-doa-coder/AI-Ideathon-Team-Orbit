import { Link } from "react-router-dom";
import { useLanguage } from "../../context/LanguageContext";
import { useHomeContent } from "../../data/useHomeContent";

/**
 * Agriva's footer-section-2.
 *
 * footerLinks entries carry either `to` (an in-app route) or `href` (an
 * on-page anchor), so each one picks <Link> or <a> accordingly — using <a
 * href="/chat"> instead would trigger a full page reload and drop the SPA's
 * auth state.
 */
function FooterList({ heading, links }) {
  return (
    <div className="single-footer-widget">
      <div className="widget-head">
        <h4>{heading}</h4>
      </div>
      <ul className="list-area">
        {links.map((link) => (
          <li key={link.label}>
            {link.to ? (
              <Link to={link.to}>
                <i className="fa-solid fa-chevron-right" />
                {link.label}
              </Link>
            ) : (
              <a href={link.href}>
                <i className="fa-solid fa-chevron-right" />
                {link.label}
              </a>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function SiteFooter() {
  const { t } = useLanguage();
  const { footerLinks, contactInfo, socialLinks } = useHomeContent();

  return (
    <footer className="footer-section-2 footer-bg fix pb-0" id="footer">
      <div className="left-shape float-bob-x">
        <img src="/assets/img/home-2/maize-tree-2.png" alt="" />
      </div>
      <div className="right-shape float-bob-x">
        <img src="/assets/img/home-2/maize-tree.png" alt="" />
      </div>

      <div className="container">
        <div className="footer-top-item">
          <div className="footer-logo wow fadeInUp" data-wow-delay=".2s">
            <Link to="/">
              <img src="/assets/img/logo-mark.png" alt="Green Leaf AI" />
            </Link>
          </div>
          <div className="footer-right-item">
            <div className="social-icon wow fadeInUp" data-wow-delay=".4s">
              {socialLinks.map((social) => (
                <a key={social.label} href={social.href} aria-label={social.label}>
                  <i className={social.icon} />
                </a>
              ))}
            </div>
            <div className="icon-item wow fadeInUp" data-wow-delay=".6s">
              <div className="icon">
                <img src="/assets/img/home-2/icon/10.svg" alt="" />
              </div>
              <div className="cont">
                <span>{t("home.footer.callForDetails")}</span>
                <h4>
                  <a href={`tel:${contactInfo.phone.replace(/\s/g, "")}`}>{contactInfo.phone}</a>
                </h4>
              </div>
            </div>
            <div className="icon-item wow fadeInUp" data-wow-delay=".8s">
              <div className="icon">
                <img src="/assets/img/home-2/icon/11.svg" alt="" />
              </div>
              <div className="cont">
                <span>{t("home.footer.emailUs")}</span>
                <h4>
                  <a href={`mailto:${contactInfo.email}`}>{contactInfo.email}</a>
                </h4>
              </div>
            </div>
          </div>
        </div>

        <div className="footer-widget-wrapper footer-widget-wrapper-2">
          <div className="row">
            <div className="col-xl-5 col-md-7 col-lg-6 wow fadeInUp" data-wow-delay=".2s">
              <div className="single-footer-widget">
                <div
                  className="footer-contact-image bg-cover"
                  style={{ backgroundImage: "url(/assets/img/home-2/vutta.jpg)" }}
                >
                  <div className="footer-contact-content">
                    <h3>{t("home.footer.newsletterHeading")}</h3>
                    {/* No newsletter backend exists yet; submitting would reload
                        the SPA, so the default action is suppressed. */}
                    <form className="wow fadeInUp" data-wow-delay=".5s" onSubmit={(e) => e.preventDefault()}>
                      <div className="form-clt">
                        <input
                          type="email"
                          name="email"
                          id="newsletterEmail"
                          placeholder={t("home.footer.emailPlaceholder")}
                        />
                        <button type="submit" className="theme-btn-2">
                          {t("home.footer.subscribe")}
                        </button>
                        <i className="fa-solid fa-envelope" />
                      </div>
                    </form>
                    <div className="input-single input-check payment-save">
                      <input
                        type="checkbox"
                        className="form-check-input"
                        name="save-for-next"
                        id="saveForNext"
                      />
                      <label htmlFor="saveForNext">{t("home.footer.agreeTerms")}</label>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="col-xl-3 col-md-5 col-lg-4 ps-lg-5 wow fadeInUp" data-wow-delay=".4s">
              <FooterList heading={t("home.footer.services")} links={footerLinks.services} />
            </div>
            <div className="col-xl-2 col-md-6 col-lg-2 wow fadeInUp" data-wow-delay=".6s">
              <FooterList heading={t("home.footer.resources")} links={footerLinks.resources} />
            </div>
            <div className="col-xl-2 ps-lg-5 col-md-6 col-lg-4 wow fadeInUp" data-wow-delay=".8s">
              <FooterList heading={t("home.footer.company")} links={footerLinks.company} />
            </div>
          </div>
        </div>

        <div className="footer-bottom pb-0">
          <div className="footer-wrapper justify-content-center">
            <p>{t("home.footer.copyright")}</p>
          </div>
        </div>
      </div>
    </footer>
  );
}
