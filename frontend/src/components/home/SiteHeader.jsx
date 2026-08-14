import { Link } from "react-router-dom";
import { useLanguage } from "../../context/LanguageContext";
import { useHomeContent } from "../../data/useHomeContent";

/**
 * Agriva's header-1, ported verbatim in structure.
 *
 * The class names and ids here are contracts with assets/js/main.js and
 * main.css, not styling choices:
 *   #header-sticky   — main.js toggles .sticky on scroll
 *   #mobile-menu     — meanmenu clones this <nav> into .mobile-menu
 *   .sidebar__toggle — opens the offcanvas drawer
 *   .search_btn      — opens .search_popup
 *   .has-dropdown    — drives the desktop submenu CSS and meanmenu's expanders
 * Renaming any of them silently drops the behaviour.
 *
 * What differs from the template: the demo nav (four homepage variants, shop,
 * portfolio, team, 404) is replaced with Green Leaf's real destinations, since
 * those pages do not exist here and would 404. The markup shape around them —
 * the mega-menu thumbnail grid, the nested submenus — is unchanged.
 */
export default function SiteHeader() {
  const { t } = useLanguage();
  const { megaMenuCards, contactInfo } = useHomeContent();

  return (
    <header id="header-sticky" className="header-1">
      <div className="container-fluid">
        <div className="mega-menu-wrapper">
          <div className="header-main">
            <div className="header-left">
              <div className="logo">
                <Link to="/" className="header-logo">
                  <img src="/assets/img/logo-mark.png" alt="Green Leaf AI" />
                </Link>
                <Link to="/" className="header-logo-2">
                  <img src="/assets/img/logo-mark.png" alt="Green Leaf AI" />
                </Link>
              </div>
            </div>

            <div className="mean__menu-wrapper">
              <div className="main-menu">
                <nav id="mobile-menu">
                  <ul>
                    {/* Mega menu — Agriva's thumbnail grid, pointed at the app's routes */}
                    <li className="has-dropdown active menu-thumb">
                      <a href="#top">{t("home.siteHeader.navHome")}</a>
                      <ul className="submenu has-homemenu">
                        <li>
                          <div className="homemenu-items">
                            {megaMenuCards.map((card, i) => (
                              <div className="homemenu" key={card.title}>
                                <div className={`homemenu-thumb${i > 0 ? " mb-15" : ""}`}>
                                  <img src={card.thumb} alt="" />
                                  <div className="demo-button">
                                    <Link to={card.href} className="theme-btn-2">
                                      {card.cta}
                                    </Link>
                                  </div>
                                </div>
                                <div className="homemenu-content text-center">
                                  <h4 className="homemenu-title">{card.title}</h4>
                                </div>
                              </div>
                            ))}
                          </div>
                        </li>
                      </ul>
                    </li>

                    {/* Mobile-only flattened Home list, exactly as the template does it */}
                    <li className="has-dropdown active d-xl-none">
                      <a href="#top" className="border-none">
                        {t("home.siteHeader.navHome")}
                      </a>
                      <ul className="submenu">
                        {megaMenuCards.map((card) => (
                          <li key={card.title}>
                            <Link to={card.href}>{card.title}</Link>
                          </li>
                        ))}
                      </ul>
                    </li>

                    <li>
                      <Link to="/about">{t("home.siteHeader.navAbout")}</Link>
                    </li>

                    <li className="has-dropdown">
                      <Link to="/services">{t("home.siteHeader.navServices")}</Link>
                      <ul className="submenu">
                        <li>
                          <Link to="/services">{t("services.heading")}</Link>
                        </li>
                        <li>
                          <Link to="/about#how-it-works">{t("home.process.subTitle")}</Link>
                        </li>
                        <li>
                          <Link to="/consultancy">{t("home.siteHeader.cropDoctor")}</Link>
                        </li>
                      </ul>
                    </li>

                    <li className="has-dropdown">
                      <Link to="/blog">{t("home.siteHeader.navBlog")}</Link>
                      <ul className="submenu">
                        <li>
                          <Link to="/blog">{t("home.siteHeader.navBlog")}</Link>
                        </li>
                        <li>
                          <Link to="/services#faq">{t("home.siteHeader.navFaq")}</Link>
                        </li>
                      </ul>
                    </li>

                    <li>
                      <Link to="/contact">{t("home.siteHeader.navContact")}</Link>
                    </li>
                  </ul>
                </nav>
              </div>
            </div>

            <div className="header-right d-flex justify-content-end align-items-center">
              <div className="icon-items">
                <div className="menu_search">
                  <button className="search_btn" type="button" aria-label="Search">
                    <i className="far fa-search" />
                  </button>
                </div>
                <Link to="/chat" aria-label={t("home.siteHeader.cropDoctor")}>
                  <i className="fa-solid fa-comment-dots" />
                </Link>
              </div>
              <div className="header-btn">
                <span>
                  <i className="fa-solid fa-phone-volume" />
                  <a href={`tel:${contactInfo.phone.replace(/\s/g, "")}`}>{contactInfo.phone}</a>
                </span>
                <div className="header-button">
                  <Link to="/chat" className="theme-btn-2 style-btns">
                    {t("home.siteHeader.askCropDoctor")}
                  </Link>
                </div>
                <div className="header__hamburger d-xl-none my-auto">
                  <div className="sidebar__toggle">
                    <i className="fas fa-bars" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
