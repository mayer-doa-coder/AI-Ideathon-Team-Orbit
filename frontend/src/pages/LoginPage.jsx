import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import "../styles/auth.css";

export default function LoginPage() {
  const { isAuthenticated, login, register } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (isAuthenticated) {
    return <Navigate to="/chat" replace />;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      if (mode === "login") {
        await login(username.trim(), password);
      } else {
        await register(username.trim(), password);
      }
      navigate("/chat");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  function toggleMode() {
    setMode((m) => (m === "login" ? "register" : "login"));
    setError("");
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <span className="auth-brand-mark">
            <img src="/assets/img/logo-mark.png" alt="" />
          </span>
          {t("loginPage.brand")}
        </div>

        <h1>{mode === "login" ? t("loginPage.welcomeBack") : t("loginPage.createAccount")}</h1>
        <p className="auth-subtitle">
          {mode === "login" ? t("loginPage.loginSubtitle") : t("loginPage.registerSubtitle")}
        </p>

        <form onSubmit={handleSubmit}>
          <div className="auth-field">
            <label htmlFor="username">{t("loginPage.username")}</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              minLength={3}
              required
            />
          </div>

          <div className="auth-field">
            <label htmlFor="password">{t("loginPage.password")}</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              minLength={6}
              required
            />
          </div>

          {error && <div className="auth-error">{error}</div>}

          <button type="submit" className="auth-submit" disabled={isSubmitting}>
            {isSubmitting
              ? t("loginPage.pleaseWait")
              : mode === "login"
                ? t("loginPage.logIn")
                : t("loginPage.createAccountButton")}
          </button>
        </form>

        <button type="button" className="auth-toggle" onClick={toggleMode}>
          {mode === "login" ? t("loginPage.toggleToRegister") : t("loginPage.toggleToLogin")}
        </button>
      </div>
    </div>
  );
}
