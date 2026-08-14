import { useState } from "react";
import { useLanguage } from "../context/LanguageContext";
import { searchKnowledgeBase } from "../services/ragApi";
import "../styles/ragTest.css";

export default function RagTestPage() {
  const { t, tf } = useLanguage();
  const [query, setQuery] = useState("");
  const [crop, setCrop] = useState("");
  const [topic, setTopic] = useState("");
  const [results, setResults] = useState(null);
  const [error, setError] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!query.trim()) return;

    setError("");
    setIsSearching(true);
    setResults(null);

    try {
      const data = await searchKnowledgeBase(query.trim(), { crop: crop.trim(), topic: topic.trim() });
      setResults(data.results);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSearching(false);
    }
  }

  return (
    <div className="rag-test-page">
      <div className="rag-test-card">
        <h1>{t("ragTestPage.title")}</h1>
        <p className="rag-test-subtitle">{t("ragTestPage.subtitle")}</p>

        <form onSubmit={handleSubmit} className="rag-test-form">
          <input
            type="text"
            placeholder={t("ragTestPage.placeholder")}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            required
          />
          <div className="rag-test-filters">
            <input
              type="text"
              placeholder={t("ragTestPage.cropFilterPlaceholder")}
              value={crop}
              onChange={(e) => setCrop(e.target.value)}
            />
            <input
              type="text"
              placeholder={t("ragTestPage.topicFilterPlaceholder")}
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />
          </div>
          <button type="submit" disabled={isSearching}>
            {isSearching ? t("ragTestPage.searching") : t("ragTestPage.search")}
          </button>
        </form>

        {error && <div className="rag-test-error">{error}</div>}

        {results && (
          <div className="rag-test-results">
            <p className="rag-test-count">{tf("ragTestPage.countTemplate", { count: results.length })}</p>
            {results.map((chunk, i) => (
              <div key={i} className="rag-chunk-card">
                <div className="rag-chunk-meta">
                  <span className="rag-chunk-score">
                    {tf("ragTestPage.similarityTemplate", { value: chunk.similarity })}
                  </span>
                  {chunk.crop && (
                    <span className="rag-chunk-tag">{tf("ragTestPage.cropTemplate", { value: chunk.crop })}</span>
                  )}
                  {chunk.topic && (
                    <span className="rag-chunk-tag">{tf("ragTestPage.topicTemplate", { value: chunk.topic })}</span>
                  )}
                  {chunk.page_number && (
                    <span className="rag-chunk-tag">
                      {tf("ragTestPage.pageTemplate", { value: chunk.page_number })}
                    </span>
                  )}
                </div>
                {chunk.section_heading && <div className="rag-chunk-heading">{chunk.section_heading}</div>}
                <p className="rag-chunk-content">{chunk.content}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
