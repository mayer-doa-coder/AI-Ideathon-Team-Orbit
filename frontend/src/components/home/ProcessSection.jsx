import { useEffect, useRef } from "react";
import { useLanguage } from "../../context/LanguageContext";
import { useHomeContent } from "../../data/useHomeContent";
import { onAgrivaBooted } from "../../utils/agrivaTemplate";
import "../../styles/process.css";

/**
 * "How it works" — the seven steps the conversation agent runs, followed by
 * the monitor-agent loop that keeps running afterwards.
 *
 * The animation is scroll-scrubbed rather than a one-shot reveal: the rail
 * fills in proportion to how far through the section you are, and each step
 * lights up as its node passes the fill. That is the point of the section —
 * the loop at the end reads as a loop only if you can see the line reach it.
 *
 * Registration goes through onAgrivaBooted() instead of a plain effect. The
 * template's boot kills every ScrollTrigger on the page and then creates the
 * ScrollSmoother, so triggers made before that are destroyed, and any made
 * before the smoother exists measure the wrong scroll positions. See the notes
 * in utils/agrivaTemplate.js.
 */
export default function ProcessSection() {
  const { t } = useLanguage();
  const { processSteps } = useHomeContent();
  const sectionRef = useRef(null);

  useEffect(() => {
    const section = sectionRef.current;
    if (!section) return undefined;

    const unsubscribe = onAgrivaBooted(() => {
      const { gsap, ScrollTrigger } = window;
      if (!gsap || !ScrollTrigger) return;

      const fill = section.querySelector(".agri-flow-rail-fill");
      const steps = Array.from(section.querySelectorAll(".agri-flow-step"));
      const rail = section.querySelector(".agri-flow-rail");
      if (!fill || !rail || !steps.length) return;

      const created = [];
      const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

      // The rail fills from the first node to the last as the section crosses
      // the middle of the viewport.
      created.push(
        ScrollTrigger.create({
          id: "agrisense-process-rail",
          trigger: rail,
          start: "top 65%",
          end: "bottom 55%",
          scrub: 0.6,
          onUpdate: (self) => {
            gsap.set(fill, { height: `${self.progress * 100}%` });
          },
        })
      );

      // Each step owns the highlight for the stretch of scroll it occupies.
      steps.forEach((step, i) => {
        created.push(
          ScrollTrigger.create({
            id: `agrisense-process-step-${i}`,
            trigger: step,
            start: "top 65%",
            end: "bottom 45%",
            onToggle: (self) => step.classList.toggle("is-active", self.isActive),
          })
        );
      });

      // Entrance: cards ease in from the rail side, staggered by position.
      if (!reduceMotion) {
        steps.forEach((step) => {
          const card = step.querySelector(".agri-flow-card");
          const node = step.querySelector(".agri-flow-node");
          created.push(
            gsap.from([node, card], {
              opacity: 0,
              x: -28,
              duration: 0.6,
              ease: "power2.out",
              stagger: 0.08,
              scrollTrigger: {
                id: "agrisense-process-enter",
                trigger: step,
                start: "top 85%",
                once: true,
              },
            }).scrollTrigger
          );
        });
      }

      return () => created.forEach((instance) => instance?.kill?.());
    });

    return unsubscribe;
  }, [processSteps]);

  return (
    <section className="agri-flow-section section-padding fix" id="how-it-works" ref={sectionRef}>
      <div className="agri-flow-grid-bg" />

      <div className="container">
        <div className="section-title text-center">
          <span className="sub-title-2">
            <img src="/assets/img/home-2/icon/04.svg" alt="" /> {t("home.process.subTitle")}
            <img src="/assets/img/home-2/icon/04.svg" alt="" className="ms-2" />
          </span>
          <h2 className="text-anim">
            {t("home.process.heading1")} <br />
            {t("home.process.heading2")}
          </h2>
        </div>

        <div className="agri-flow-timeline">
          <div className="agri-flow-rail">
            <div className="agri-flow-rail-fill" />
          </div>

          {processSteps.map((step, i) => (
            <div
              className={`agri-flow-step${step.isLoop ? " is-loop" : ""}`}
              key={step.title}
            >
              <div className="agri-flow-node">
                {step.isLoop ? <i className={step.icon} /> : String(i + 1).padStart(2, "0")}
              </div>
              <div className="agri-flow-card">
                <h3>{step.title}</h3>
                <p>{step.text}</p>
                {step.meta && (
                  <span className="agri-flow-meta">
                    <i className={step.isLoop ? "fa-solid fa-rotate" : "fa-solid fa-bolt"} />
                    {step.meta}
                  </span>
                )}
                {step.isLoop && (
                  <div className="agri-flow-loop-note">
                    <i className="fa-solid fa-arrows-rotate" />
                    {t("home.process.loopNote")}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
