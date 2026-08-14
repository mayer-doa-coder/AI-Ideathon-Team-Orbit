import { Link } from "react-router-dom";
import { useLanguage } from "../../context/LanguageContext";
import "../../styles/marketing.css";

/**
 * Agriva's breadcrumb-wrapper, used as the page header on every inner
 * marketing route. Markup mirrors about.html so main.css and the WOW reveals
 * apply unchanged.
 */
export default function Breadcrumb({ title }) {
  const { t } = useLanguage();

  return (
    <div
      className="breadcrumb-wrapper bg-cover"
      style={{ backgroundImage: "url('/assets/img/breadcrumb.png')" }}
    >
      <div className="top-image">
        <img src="/assets/img/breadcrumb-2.jpg" alt="" />
      </div>
      <div className="container">
        <div className="page-heading">
          <div className="breadcrumb-sub-title">
            <h1 className="text-white wow fadeInUp" data-wow-delay=".3s">
              {title}
            </h1>
          </div>
          <ul className="breadcrumb-items wow fadeInUp" data-wow-delay=".5s">
            <li>
              <Link to="/">
                <i className="fa-solid fa-house" /> {t("home.siteHeader.navHome")}
              </Link>
            </li>
            <li>:</li>
            <li>{title}</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
