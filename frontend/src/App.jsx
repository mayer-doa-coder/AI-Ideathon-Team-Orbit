import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { LanguageProvider } from "./context/LanguageContext";
import RequireAuth from "./components/auth/RequireAuth";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import ChatPage from "./pages/ChatPage";
import RagTestPage from "./pages/RagTestPage";
import AskPage from "./pages/AskPage";
import PaymentPage from "./pages/PaymentPage";
import ConsultancyPage from "./pages/ConsultancyPage";
import "./styles/chat.css";

function App() {
  return (
    <BrowserRouter>
      <LanguageProvider>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/rag-test" element={<RagTestPage />} />
            <Route path="/ask" element={<AskPage />} />
            <Route
              path="/chat"
              element={
                <RequireAuth>
                  <ChatPage />
                </RequireAuth>
              }
            />
            <Route
              path="/payment"
              element={
                <RequireAuth>
                  <PaymentPage />
                </RequireAuth>
              }
            />
            <Route
              path="/consultancy"
              element={
                <RequireAuth>
                  <ConsultancyPage />
                </RequireAuth>
              }
            />
          </Routes>
        </AuthProvider>
      </LanguageProvider>
    </BrowserRouter>
  );
}

export default App;
