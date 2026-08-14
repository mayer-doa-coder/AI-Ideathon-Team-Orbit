import { useState } from "react";
import { useLanguage } from "../../context/LanguageContext";

export default function Carousel({ items, renderItem, className = "" }) {
  const { t } = useLanguage();
  const [index, setIndex] = useState(0);

  function prev() {
    setIndex((i) => (i - 1 + items.length) % items.length);
  }

  function next() {
    setIndex((i) => (i + 1) % items.length);
  }

  return (
    <div className={`carousel ${className}`}>
      <div className="carousel-track">{renderItem(items[index], index)}</div>
      {items.length > 1 && (
        <div className="carousel-controls">
          <button type="button" onClick={prev} aria-label={t("home.carousel.previous")}>
            <i className="fa-solid fa-arrow-left" />
          </button>
          <div className="carousel-dots">
            {items.map((_, i) => (
              <span
                key={i}
                className={i === index ? "dot active" : "dot"}
                onClick={() => setIndex(i)}
              />
            ))}
          </div>
          <button type="button" onClick={next} aria-label={t("home.carousel.next")}>
            <i className="fa-solid fa-arrow-right" />
          </button>
        </div>
      )}
    </div>
  );
}
