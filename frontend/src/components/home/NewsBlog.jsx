import { Link } from "react-router-dom";
import { useLanguage } from "../../context/LanguageContext";
import { useHomeContent } from "../../data/useHomeContent";

/**
 * Agriva's news-section-2.
 *
 * item_right_1 / item_left_1 on the outer columns are GSAP slide-in triggers
 * from main.js — the first card enters from the right, the last from the left,
 * and the middle one stays put, so the classes are position-dependent rather
 * than per-card.
 *
 * The template's second meta chip is a hardcoded comment count. There is no
 * comment system here, so rather than print a fabricated number the chip is
 * dropped and only the real publication date is shown.
 */
export default function NewsBlog() {
  const { t } = useLanguage();
  const { blogPosts } = useHomeContent();

  return (
    <section className="news-section-2 section-padding fix" id="blog">
      <div className="container">
        <div className="section-title text-center">
          <span className="sub-title-2">
            <img src="/assets/img/home-2/icon/04.svg" alt="" /> {t("home.newsBlog.subTitle")}
            <img src="/assets/img/home-2/icon/04.svg" alt="" className="ms-2" />
          </span>
          <h2 className="text-anim">{t("home.newsBlog.heading")}</h2>
        </div>

        <div className="row">
          {blogPosts.map((post, i) => {
            const edge =
              i === 0 ? " item_right_1" : i === blogPosts.length - 1 ? " item_left_1" : "";
            return (
              <div className={`col-xl-4 col-lg-6 col-md-6${edge}`} key={post.title}>
                <div className="news-card-items-2">
                  <div className="news-image">
                    <img src={`/assets/img/home-2/news/0${(i % 3) + 1}.jpg`} alt="" />
                    <Link to="/chat" className="theme-btn-2">
                      {t("home.newsBlog.readMore")}
                    </Link>
                    <div className="news-content">
                      <h3>
                        <Link to="/chat">{post.title}</Link>
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
            );
          })}
        </div>
      </div>
    </section>
  );
}
