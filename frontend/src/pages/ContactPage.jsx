import { useState } from "react";
import { Link } from "react-router-dom";
import MarketingLayout from "../components/marketing/MarketingLayout";
import Breadcrumb from "../components/marketing/Breadcrumb";
import { useLanguage } from "../context/LanguageContext";
import { useHomeContent } from "../data/useHomeContent";

/**
 * /contact — contact details, the quickest routes into the product, and a
 * message form.
 *
 * There is no contact-form endpoint on the backend, so the form does not
 * pretend to send. It validates, then tells the visitor plainly to email
 * instead and offers a mailto link pre-filled with what they typed — which is
 * honest and still gets the message delivered, unlike a fake success toast.
 */
export default function ContactPage() {
  const { t } = useLanguage();
  const { contactInfo, socialLinks } = useHomeContent();

  const [form, setForm] = useState({ name: "", email: "", subject: "", message: "" });
  const [submitted, setSubmitted] = useState(false);

  const update = (field) => (event) => setForm({ ...form, [field]: event.target.value });

  const mailtoHref = `mailto:${contactInfo.email}?subject=${encodeURIComponent(
    form.subject || `Message from ${form.name || "the Green Leaf site"}`
  )}&body=${encodeURIComponent(`${form.message}\n\n— ${form.name}\n${form.email}`)}`;

  return (
    <MarketingLayout>
      <Breadcrumb title={t("contact.title")} />

      <section className="section-padding fix">
        <div className="container">
          <div className="row g-4">
            {/* Contact details */}
            <div className="col-lg-5">
              <div className="section-title">
                <span className="sub-title-2">
                  <img src="/assets/img/home-2/icon/04.svg" alt="" /> {t("contact.eyebrow")}
                </span>
                <h2 className="text-anim">{t("contact.heading")}</h2>
              </div>
              <p>{contactInfo.blurb}</p>

              <div className="offcanvas__contact mt-4">
                <ul>
                  <li className="d-flex align-items-center">
                    <div className="offcanvas__contact-icon style-2 mr-15">
                      <i className="fal fa-map-marker-alt" />
                    </div>
                    <div className="offcanvas__contact-text">{contactInfo.address}</div>
                  </li>
                  <li className="d-flex align-items-center">
                    <div className="offcanvas__contact-icon style-2 mr-15">
                      <i className="fal fa-envelope" />
                    </div>
                    <div className="offcanvas__contact-text">
                      <a href={`mailto:${contactInfo.email}`}>{contactInfo.email}</a>
                    </div>
                  </li>
                  <li className="d-flex align-items-center">
                    <div className="offcanvas__contact-icon style-2 mr-15">
                      <i className="far fa-phone" />
                    </div>
                    <div className="offcanvas__contact-text">
                      <a href={`tel:${contactInfo.phone.replace(/\s/g, "")}`}>{contactInfo.phone}</a>
                    </div>
                  </li>
                  <li className="d-flex align-items-center">
                    <div className="offcanvas__contact-icon style-2 mr-15">
                      <i className="fal fa-clock" />
                    </div>
                    <div className="offcanvas__contact-text">{contactInfo.hours}</div>
                  </li>
                </ul>
                <div className="social-icon d-flex align-items-center style-2 mt-3">
                  {socialLinks.map((social) => (
                    <a key={social.label} href={social.href} aria-label={social.label}>
                      <i className={social.icon} />
                    </a>
                  ))}
                </div>
              </div>

              <div className="choose-us-box mt-4">
                <div className="content">
                  <h3>{t("contact.fastestHeading")}</h3>
                  <span>{t("contact.fastestText")}</span>
                </div>
              </div>
              <div className="mt-3 d-flex flex-wrap gap-2">
                <Link to="/chat" className="theme-btn-2">
                  {t("home.siteHeader.askCropDoctor")}
                </Link>
                <Link to="/ask" className="theme-btn-2 border-btn">
                  {t("contact.askHandbook")}
                </Link>
              </div>
            </div>

            {/* Message form.
                The .contact-wrapper > .contact-content > .contact-form nesting
                is not decorative — main.css:4780 styles the inputs only through
                that full chain, so a shorter wrapper renders them unstyled. */}
            <div className="col-lg-7">
              <div className="contact-wrapper">
                <div className="contact-content">
                  <div className="section-title mb-4">
                    <h3>{t("contact.formHeading")}</h3>
                  </div>

                  <div className="contact-form">
                    <form
                      onSubmit={(event) => {
                        event.preventDefault();
                        setSubmitted(true);
                      }}
                    >
                      <div className="row g-3">
                        <div className="col-lg-6">
                          <div className="form-clt">
                            <span>{t("contact.nameLabel")}</span>
                            <input
                              type="text"
                              required
                              placeholder={t("contact.namePlaceholder")}
                              value={form.name}
                              onChange={update("name")}
                            />
                          </div>
                        </div>
                        <div className="col-lg-6">
                          <div className="form-clt">
                            <span>{t("contact.emailLabel")}</span>
                            <input
                              type="email"
                              required
                              placeholder={t("contact.emailPlaceholder")}
                              value={form.email}
                              onChange={update("email")}
                            />
                          </div>
                        </div>
                        <div className="col-lg-12">
                          <div className="form-clt">
                            <span>{t("contact.subjectLabel")}</span>
                            <input
                              type="text"
                              placeholder={t("contact.subjectPlaceholder")}
                              value={form.subject}
                              onChange={update("subject")}
                            />
                          </div>
                        </div>
                        <div className="col-lg-12">
                          <div className="form-clt">
                            <span>{t("contact.messageLabel")}</span>
                            <textarea
                              rows="6"
                              required
                              placeholder={t("contact.messagePlaceholder")}
                              value={form.message}
                              onChange={update("message")}
                            />
                          </div>
                        </div>
                        <div className="col-lg-12">
                          <button type="submit" className="theme-btn">
                            {t("contact.submit")}
                          </button>
                        </div>
                      </div>
                    </form>

                    {submitted && (
                      <div className="choose-us-box mt-4" role="status">
                        <div className="content">
                          <h3>{t("contact.noEndpointHeading")}</h3>
                          <span>
                            {t("contact.noEndpointText")}{" "}
                            <a href={mailtoHref} className="link-btn-2">
                              {t("contact.openEmail")}
                            </a>
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </MarketingLayout>
  );
}
