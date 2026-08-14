import { Link } from "react-router-dom";
import MarketingLayout from "../components/marketing/MarketingLayout";
import Breadcrumb from "../components/marketing/Breadcrumb";
import BrandStrip from "../components/home/BrandStrip";
import { useLanguage } from "../context/LanguageContext";
import { useHomeContent } from "../data/useHomeContent";

/**
 * /blog — the engineering write-ups, expanded from the home page's three-card
 * teaser into full standfirsts.
 *
 * There is no CMS and no per-post route: each entry links to the part of the
 * product it describes rather than to a stub article page, so nothing here is
 * a dead link.
 */
export default function BlogPage() {
  const { t } = useLanguage();
  const { blogPosts } = useHomeContent();

  return (
    <MarketingLayout>
      <Breadcrumb title={t("blog.title")} />

      <section className="news-section-2 section-padding fix">
        <div className="container">
          <div className="section-title text-center">
            <span className="sub-title-2">
              <img src="/assets/img/home-2/icon/04.svg" alt="" /> {t("home.newsBlog.subTitle")}
              <img src="/assets/img/home-2/icon/04.svg" alt="" className="ms-2" />
            </span>
            <h2 className="text-anim">{t("blog.heading")}</h2>
          </div>

          <div className="row g-4">
            {blogPosts.map((post, i) => (
              <div
                className={`col-xl-4 col-lg-6 col-md-6${
                  i === 0 ? " item_right_1" : i === blogPosts.length - 1 ? " item_left_1" : ""
                }`}
                key={post.title}
              >
                <div className="news-card-items-2">
                  <div className="news-image">
                    <img src={`/assets/img/home-2/news/0${(i % 3) + 1}.jpg`} alt="" />
                    <Link to={post.to || "/chat"} className="theme-btn-2">
                      {t("home.newsBlog.readMore")}
                    </Link>
                    <div className="news-content">
                      <h3>
                        <Link to={post.to || "/chat"}>{post.title}</Link>
                      </h3>
                      <p>{post.excerpt}</p>
                      <div className="tag">
                        <span>
                          <i className="fa-regular fa-calendar" />
                          {post.date}
                        </span>
                        <span>
                          <i className={post.icon} />
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* The long-form documentation actually lives in the repository, so
              point there rather than inventing article pages. */}
          <div className="faq-box mt-5">
            <div className="section-title mb-4">
              <h3>{t("blog.docsHeading")}</h3>
            </div>
            <p>{t("blog.docsIntro")}</p>
            <ul className="list-area mt-3">
              <li>
                <i className="fa-solid fa-chevron-right" /> <strong>README.md</strong> —{" "}
                {t("blog.docsReadme")}
              </li>
              <li>
                <i className="fa-solid fa-chevron-right" /> <strong>PROJECT_OVERVIEW.md</strong> —{" "}
                {t("blog.docsOverview")}
              </li>
              <li>
                <i className="fa-solid fa-chevron-right" />{" "}
                <strong>CONVERSATION_AGENT_EXPLAINED.md</strong> — {t("blog.docsAgent")}
              </li>
              <li>
                <i className="fa-solid fa-chevron-right" /> <strong>TIER_1_FEATURES.md</strong> —{" "}
                {t("blog.docsTier1")}
              </li>
            </ul>
          </div>
        </div>
      </section>

      <BrandStrip />
    </MarketingLayout>
  );
}
