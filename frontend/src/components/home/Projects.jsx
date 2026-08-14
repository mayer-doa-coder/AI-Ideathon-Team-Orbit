import { Link } from "react-router-dom";
import { useLanguage } from "../../context/LanguageContext";
import { useHomeContent } from "../../data/useHomeContent";

/**
 * Agriva's project-section-2 — a ScrollTrigger-pinned section where scrolling
 * steps through the left-hand list and cross-fades the large thumbnail.
 *
 * main.js refuses to wire this up unless
 *   .project-left-item .project-image  count === .project-thumb .thumb-img count
 * so the same `projects` array drives both columns; see the note on `projects`
 * in data/homeContent.js. The empty <span> in each row is not filler — main.js
 * recolours it to mark the active item.
 */
export default function Projects() {
  const { t } = useLanguage();
  const { projects } = useHomeContent();

  return (
    <section className="project-section-2 section-padding fix" id="projects">
      <div className="container">
        <div className="section-title text-center">
          <span className="sub-title-2">
            <img src="/assets/img/home-2/icon/04.svg" alt="" /> {t("home.projects.subTitle")}
            <img src="/assets/img/home-2/icon/04.svg" alt="" className="ms-2" />
          </span>
          <h2 className="text-anim">
            {t("home.projects.heading1")} <br />
            {t("home.projects.heading2")}
          </h2>
        </div>

        <div className="project-wrapper-2">
          <div className="row g-4">
            <div className="col-xl-4 col-lg-5">
              <div className="project-left-item">
                {projects.map((project) => (
                  <div className="project-image" data-thumb={project.image} key={project.title}>
                    <img src={project.image} alt="" />
                    <div className="project-content">
                      {/* active-state marker, recoloured by main.js */}
                      <span />
                      <h3>
                        <Link to="/chat">{project.title}</Link>
                      </h3>
                      <div className="tag">
                        {project.tags.map((tag) => (
                          <h4 key={tag}>{tag}</h4>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="col-xl-8 col-lg-7">
              <div className="project-thumb-item">
                <div className="project-thumb">
                  {projects.map((project, i) => (
                    <img
                      key={project.thumb}
                      src={project.thumb}
                      className={`thumb-img${i === 0 ? " active" : ""}`}
                      alt=""
                    />
                  ))}
                  <h2>01</h2>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
