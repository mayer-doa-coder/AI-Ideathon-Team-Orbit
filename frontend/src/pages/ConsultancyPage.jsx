import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  createConsultation,
  getConsultancyAccess,
  getConsultations,
  getExperts,
} from "../services/consultancyApi";
import "../styles/consultancy.css";

export default function ConsultancyPage() {
  const { token } = useAuth();

  const [access, setAccess] = useState(null);
  const [experts, setExperts] = useState([]);
  const [consultations, setConsultations] = useState([]);
  const [selectedExpertId, setSelectedExpertId] = useState("");
  const [topic, setTopic] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setIsLoading(true);
      setError("");
      try {
        const [accessData, expertsData, consultationsData] = await Promise.all([
          getConsultancyAccess(token),
          getExperts(token),
          getConsultations(token),
        ]);
        if (cancelled) return;
        setAccess(accessData);
        setExperts(expertsData);
        setConsultations(consultationsData);
        if (expertsData.length > 0) setSelectedExpertId(expertsData[0].id);
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [token]);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!selectedExpertId || !topic.trim()) return;

    setError("");
    setIsSubmitting(true);
    try {
      const created = await createConsultation(token, { expertId: selectedExpertId, topic: topic.trim() });
      setConsultations((prev) => [created, ...prev]);
      setTopic("");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  const hasPremium = access?.has_premium;

  return (
    <div className="consultancy-page">
      <div className="consultancy-container">
        <header className="consultancy-header">
          <Link to="/chat" className="consultancy-back-link">
            &larr; Back to dashboard
          </Link>
          <h1>Expert Crop Consultancy</h1>
          <p className="consultancy-subtitle">
            Get personalised guidance from agronomists, plant pathologists and soil specialists —
            a premium service unlocked by your AgriSense payment.
          </p>
        </header>

        {isLoading ? (
          <div className="consultancy-loading">Loading consultancy desk...</div>
        ) : !hasPremium ? (
          <LockedState experts={experts} />
        ) : (
          <div className="consultancy-body">
            <section className="consultancy-panel consultancy-ask">
              <div className="consultancy-premium-badge">
                Premium active
                <span>{access.successful_payments} payment{access.successful_payments === 1 ? "" : "s"}</span>
              </div>
              <h2>Ask a crop expert</h2>

              <form onSubmit={handleSubmit}>
                <label className="consultancy-label">Choose an expert</label>
                <div className="expert-grid">
                  {experts.map((expert) => (
                    <button
                      type="button"
                      key={expert.id}
                      className={`expert-card ${selectedExpertId === expert.id ? "selected" : ""}`}
                      onClick={() => setSelectedExpertId(expert.id)}
                    >
                      <span className="expert-avatar">{expert.avatar_initials}</span>
                      <span className="expert-info">
                        <span className="expert-name">{expert.name}</span>
                        <span className="expert-specialty">{expert.specialty}</span>
                        <span className="expert-credentials">{expert.credentials}</span>
                      </span>
                    </button>
                  ))}
                </div>

                <label className="consultancy-label" htmlFor="topic">
                  Your question
                </label>
                <textarea
                  id="topic"
                  placeholder="Describe your crop, the problem you're seeing, your district and soil type..."
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  rows={4}
                  required
                />

                {error && <div className="consultancy-error">{error}</div>}

                <button type="submit" className="consultancy-submit" disabled={isSubmitting || !topic.trim()}>
                  {isSubmitting ? "Sending to expert..." : "Send to expert"}
                </button>
              </form>
            </section>

            <section className="consultancy-panel consultancy-thread">
              <h2>Your consultations</h2>
              {consultations.length === 0 ? (
                <p className="consultancy-empty">No consultations yet. Ask your first question.</p>
              ) : (
                <ul className="consultation-list">
                  {consultations.map((c) => (
                    <li key={c.id} className="consultation-item">
                      <div className="consultation-question">
                        <span className="consultation-role">You</span>
                        <p>{c.topic}</p>
                      </div>
                      <div className="consultation-answer">
                        <span className="consultation-role expert">
                          {c.expert_name} · {c.expert_specialty}
                        </span>
                        <p>{c.expert_reply}</p>
                      </div>
                      <span className="consultation-meta">
                        {new Date(c.created_at).toLocaleString()} · {c.status}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        )}
      </div>
    </div>
  );
}

function LockedState({ experts }) {
  return (
    <div className="consultancy-locked">
      <div className="consultancy-lock-card">
        <span className="consultancy-lock-icon">
          <i className="fa-solid fa-lock" />
        </span>
        <h2>Unlock Expert Consultancy</h2>
        <p>
          One-to-one advice from crop experts is a premium feature. Complete a payment through
          AgriSense Premium to start asking questions and get tailored guidance.
        </p>
        <Link to="/payment" className="consultancy-unlock-btn">
          Unlock with Premium
        </Link>
      </div>

      <div className="consultancy-preview">
        <h3>Experts you'll be able to reach</h3>
        <div className="expert-grid preview">
          {experts.map((expert) => (
            <div key={expert.id} className="expert-card locked">
              <span className="expert-avatar">{expert.avatar_initials}</span>
              <span className="expert-info">
                <span className="expert-name">{expert.name}</span>
                <span className="expert-specialty">{expert.specialty}</span>
                <span className="expert-credentials">{expert.credentials}</span>
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
