import { Link } from "react-router-dom";
import { useLanguage } from "../../context/LanguageContext";
import { useHomeContent } from "../../data/useHomeContent";

function FooterLink({ label, href, to }) {
  if (to) {
    return (
      <li>
        <Link to={to}>
          <i className="fa-solid fa-chevron-right" /> {label}
        </Link>
      </li>
    );
  }
  return (
    <li>
      <a href={href}>
        <i className="fa-solid fa-chevron-right" /> {label}
      </a>
    </li>
  );
}

export default function SiteFooter() {
  const { t } = useLanguage();
  const { footerLinks } = useHomeContent();

  return (
    <footer className="site-footer" id="footer">
      <div className="section-inner">
        <div className="footer-top">
          <a href="#top" className="site-logo light">
            <span className="site-logo-mark">
              <i className="fa-solid fa-leaf" />
            </span>
            {t("home.siteHeader.brand")}
          </a>
          <div className="footer-top-right">
            <div className="social-icons">
              <a href="#"><i className="fa-brands fa-facebook-f" /></a>
              <a href="#"><i className="fa-brands fa-linkedin-in" /></a>
              <a href="#"><i className="fa-brands fa-twitter" /></a>
              <a href="#"><i className="fa-brands fa-youtube" /></a>
            </div>
            <div className="footer-contact-item">
              <i className="fa-solid fa-phone-volume" />
              <div>
                <span>{t("home.footer.callForDetails")}</span>
                <h4><a href="tel:+8801234567890">+880 1234 567890</a></h4>
              </div>
            </div>
            <div className="footer-contact-item">
              <i className="fa-solid fa-envelope" />
              <div>
                <span>{t("home.footer.emailUs")}</span>
                <h4><a href="mailto:support@agrisense.ai">support@agrisense.ai</a></h4>
              </div>
            </div>
          </div>
        </div>

        <div className="footer-widgets">
          <div className="footer-newsletter">
            <h3>{t("home.footer.newsletterHeading")}</h3>
            <form onSubmit={(e) => e.preventDefault()}>
              <input type="email" placeholder={t("home.footer.emailPlaceholder")} />
              <button type="submit" className="theme-btn-2">
                {t("home.footer.subscribe")}
              </button>
            </form>
          </div>

          <div className="footer-links-col">
            <h4>{t("home.footer.services")}</h4>
            <ul>
              {footerLinks.services.map((l) => (
                <FooterLink key={l.label} {...l} />
              ))}
            </ul>
          </div>

          <div className="footer-links-col">
            <h4>{t("home.footer.resources")}</h4>
            <ul>
              {footerLinks.resources.map((l) => (
                <FooterLink key={l.label} {...l} />
              ))}
            </ul>
          </div>

          <div className="footer-links-col">
            <h4>{t("home.footer.company")}</h4>
            <ul>
              {footerLinks.company.map((l) => (
                <FooterLink key={l.label} {...l} />
              ))}
            </ul>
          </div>
        </div>

        <div className="footer-bottom">
          <p>{t("home.footer.copyright")}</p>
        </div>
      </div>
    </footer>
  );
}
