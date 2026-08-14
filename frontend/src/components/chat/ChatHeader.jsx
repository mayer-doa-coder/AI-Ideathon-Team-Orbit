import { Link } from "react-router-dom";
import { useLanguage } from "../../context/LanguageContext";

export default function ChatHeader({ username, onLogout }) {
  const { t, toggleLanguage } = useLanguage();

  return (
    <header className="chat-header">
      <Link to="/" className="chat-header-brand">
        <span className="chat-header-mark">
          <i className="fa-solid fa-leaf" />
        </span>
        <div>
          <h1>{t("chatHeader.brand")}</h1>
          <span className="chat-header-subtitle">{t("chatHeader.subtitle")}</span>
        </div>
      </Link>

      <div className="chat-header-right">
        <button
          type="button"
          className="chat-language-toggle"
          onClick={toggleLanguage}
          aria-label={t("chatHeader.languageToggleTitle")}
          title={t("chatHeader.languageToggleTitle")}
        >
          <i className="fa-solid fa-language" />
          {t("chatHeader.languageToggleLabel")}
        </button>
        <span className="chat-header-status">
          <span className="status-dot" />
          {t("chatHeader.online")}
        </span>
        {username && (
          <div className="chat-header-user">
            <Link to="/consultancy" className="chat-header-user-name">
              <i className="fa-solid fa-user-doctor" /> Expert Consultancy
            </Link>
            <Link to="/payment" className="chat-header-user-name">
              <i className="fa-solid fa-credit-card" /> Premium
            </Link>
            <span className="chat-header-user-name">
              <i className="fa-solid fa-user" /> {username}
            </span>
            {onLogout && (
              <button type="button" className="chat-header-logout" onClick={onLogout}>
                {t("chatHeader.logout")}
              </button>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
