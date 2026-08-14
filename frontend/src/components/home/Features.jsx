import { useHomeContent } from "../../data/useHomeContent";

export default function Features() {
  const { features } = useHomeContent();
  return (
    <section className="features-section">
      <div className="section-inner">
        <div className="features-grid">
          {features.map((f) => (
            <div className="feature-card" key={f.title}>
              <div className="feature-card-icon">
                <img src={f.icon} alt="" />
              </div>
              <div className="feature-card-content">
                <h3>{f.title}</h3>
                <p>{f.text}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
