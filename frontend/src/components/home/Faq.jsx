import { useState } from "react";
import { useLanguage } from "../../context/LanguageContext";
import { useHomeContent } from "../../data/useHomeContent";

export default function Faq() {
  const { t } = useLanguage();
  const { faqStats, faqItems } = useHomeContent();
  const [openIndex, setOpenIndex] = useState(0);

  return (
    <section className="faq-section" id="faq">
      <div className="section-inner faq-grid">
        <div className="faq-content">
          <span className="sub-title light">
            <i className="fa-solid fa-leaf" /> {t("home.faq.subTitle")}
          </span>
          <h2 className="light">{t("home.faq.heading")}</h2>

          <div className="faq-progress-list">
            {faqStats.map((s) => (
              <div className="faq-progress-item" key={s.title}>
                <div className="faq-progress-head">
                  <h3>{s.title}</h3>
                  <span>{s.value}%</span>
                </div>
                <div className="faq-progress-bar">
                  <div className="faq-progress-value" style={{ width: `${s.value}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="faq-accordion">
          {faqItems.map((item, i) => (
            <div className={`faq-item ${openIndex === i ? "open" : ""}`} key={item.question}>
              <button
                type="button"
                className="faq-question"
                onClick={() => setOpenIndex(openIndex === i ? -1 : i)}
              >
                {item.question}
                <i className={`fa-solid ${openIndex === i ? "fa-minus" : "fa-plus"}`} />
              </button>
              {openIndex === i && <div className="faq-answer">{item.answer}</div>}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
