import { useState } from "react";
import { useLanguage } from "../context/LanguageContext";
import { askKnowledgeBase } from "../services/ragApi";
import "../styles/ragTest.css";

export default function AskPage() {
  const { t, tf } = useLanguage();
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [isAsking, setIsAsking] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!query.trim()) return;

    setError("");
    setIsAsking(true);
    setResult(null);

    try {
      const data = await askKnowledgeBase(query.trim());
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsAsking(false);
    }
  }

  return (
    <div className="rag-test-page">
      <div className="rag-test-card">
        <h1>{t("askPage.title")}</h1>
        <p className="rag-test-subtitle">{t("askPage.subtitle")}</p>

        <form onSubmit={handleSubmit} className="rag-test-form">
          <input
            type="text"
            placeholder={t("askPage.placeholder")}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            required
          />
          <button type="submit" disabled={isAsking}>
            {isAsking ? t("askPage.thinking") : t("askPage.ask")}
          </button>
        </form>

        {error && <div className="rag-test-error">{error}</div>}

        {result && (
          <div className="rag-test-results">
            <div className="rag-answer-card">{result.answer}</div>

            {result.sources.length > 0 && (
              <>
                <p className="rag-test-count">{tf("askPage.sourcesTemplate", { count: result.sources.length })}</p>
                {result.sources.map((chunk, i) => (
                  <div key={i} className="rag-chunk-card">
                    <div className="rag-chunk-meta">
                      <span className="rag-chunk-score">
                        {tf("askPage.similarityTemplate", { value: chunk.similarity })}
                      </span>
                      {chunk.crop && (
                        <span className="rag-chunk-tag">{tf("askPage.cropTemplate", { value: chunk.crop })}</span>
                      )}
                      {chunk.topic && (
                        <span className="rag-chunk-tag">{tf("askPage.topicTemplate", { value: chunk.topic })}</span>
                      )}
                      {chunk.page_number && (
                        <span className="rag-chunk-tag">
                          {tf("askPage.pageTemplate", { value: chunk.page_number })}
                        </span>
                      )}
                    </div>
                    <p className="rag-chunk-content">{chunk.content}</p>
                  </div>
                ))}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
