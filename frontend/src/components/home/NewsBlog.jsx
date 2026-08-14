import { useLanguage } from "../../context/LanguageContext";
import { useHomeContent } from "../../data/useHomeContent";

export default function NewsBlog() {
  const { t } = useLanguage();
  const { blogPosts } = useHomeContent();
  return (
    <section className="news-section" id="blog">
      <div className="section-inner">
        <div className="section-title">
          <span className="sub-title">
            <i className="fa-solid fa-leaf" /> {t("home.newsBlog.subTitle")}
          </span>
          <h2>{t("home.newsBlog.heading")}</h2>
        </div>

        <div className="news-grid">
          {blogPosts.map((post) => (
            <article className="news-card" key={post.title}>
              <div className="news-card-image">
                <i className={post.icon} />
              </div>
              <div className="news-card-content">
                <h3>{post.title}</h3>
                <p>{post.excerpt}</p>
                <span className="news-card-date">
                  <i className="fa-regular fa-calendar" /> {post.date}
                </span>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
