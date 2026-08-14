import { useState } from "react";
import { Link } from "react-router-dom";
import { useLanguage } from "../../context/LanguageContext";

export default function SiteHeader() {
  const { t } = useLanguage();
  const [menuOpen, setMenuOpen] = useState(false);

  const navLinks = [
    { label: t("home.siteHeader.navHome"), href: "#top" },
    { label: t("home.siteHeader.navAbout"), href: "#about" },
    { label: t("home.siteHeader.navServices"), href: "#services" },
    { label: t("home.siteHeader.navContact"), href: "#footer" },
  ];

  return (
    <header className="site-header" id="top">
      <div className="site-header-inner">
        <a href="#top" className="site-logo">
          <span className="site-logo-mark">
            <i className="fa-solid fa-leaf" />
          </span>
          {t("home.siteHeader.brand")}
        </a>

        <nav className={`site-nav ${menuOpen ? "open" : ""}`}>
          {navLinks.map((link) => (
            <a key={link.label} href={link.href} onClick={() => setMenuOpen(false)}>
              {link.label}
            </a>
          ))}
          <Link to="/chat" className="site-nav-chat" onClick={() => setMenuOpen(false)}>
            {t("home.siteHeader.cropDoctor")}
          </Link>
        </nav>

        <div className="site-header-actions">
          <Link to="/chat" className="theme-btn-2 style-btns">
            {t("home.siteHeader.askCropDoctor")}
          </Link>
          <button
            type="button"
            className="site-header-hamburger"
            aria-label={t("home.siteHeader.toggleMenu")}
            onClick={() => setMenuOpen((v) => !v)}
          >
            <i className="fa-solid fa-bars" />
          </button>
        </div>
      </div>
    </header>
  );
}
