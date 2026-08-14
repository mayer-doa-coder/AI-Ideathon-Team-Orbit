import { useLanguage } from "../../context/LanguageContext";
import FormattedText from "./FormattedText";

// audioUrl (assistant only): voice_output.audio_path's browser-fetchable
// URL, set once the "audio" SSE event lands (see ChatPage) — auto-plays,
// but text is always rendered too, never audio-only (see disease_result's
// own "never fabricate/never hide" discipline this mirrors).
// isVoice/transcriptFailed (user only): marks a bubble that originated as
// a recorded voice message rather than typed text (see ChatInput's mic
// button) — transcriptFailed means the backend's transcribe_audio call
// failed, so `text` is still just the placeholder, never a guess.
export default function ChatMessage({ role, text, image, badge, audioUrl, isVoice, transcriptFailed }) {
  const { t } = useLanguage();
  const isAssistant = role === "assistant";

  return (
    <div className={`chat-message ${isAssistant ? "assistant" : "user"}`}>
      {isAssistant && (
        <span className="chat-avatar">
          <i className="fa-solid fa-leaf" />
        </span>
      )}
      <div className="chat-bubble-stack">
        {isAssistant && badge && (
          <span className={`diagnosis-badge diagnosis-badge-${badge.level}`}>
            {badge.level === "high" ? (
              <i className="fa-solid fa-circle-check" />
            ) : (
              <i className="fa-solid fa-triangle-exclamation" />
            )}
            {badge.label}
          </span>
        )}
        <div className="chat-bubble">
          {!isAssistant && isVoice && (
            <span className="voice-message-tag">
              <i className="fa-solid fa-microphone" /> {t("chatMessage.voiceTag")}
            </span>
          )}
          {image && <img className="chat-bubble-image" src={image} alt={t("chatMessage.photoAlt")} />}
          {isAssistant && audioUrl && (
            // eslint-disable-next-line jsx-a11y/media-has-caption
            <audio className="chat-audio-player" controls autoPlay src={audioUrl} />
          )}
          {text && (isAssistant ? <FormattedText text={text} /> : text)}
          {!isAssistant && transcriptFailed && (
            <div className="voice-transcript-failed-note">{t("chatMessage.transcriptFailedNote")}</div>
          )}
        </div>
      </div>
    </div>
  );
}
