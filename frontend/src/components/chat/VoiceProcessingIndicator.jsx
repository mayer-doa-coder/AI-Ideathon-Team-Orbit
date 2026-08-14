import { useLanguage } from "../../context/LanguageContext";

// Distinct from TypingIndicator so a voice turn reads differently while
// waiting: "listening" while transcribe_audio is still running server-side,
// then "thinking" once the voice_input trace entry lands (see ChatPage's
// "trace" event handler) and the turn continues into the normal agent flow.
export default function VoiceProcessingIndicator({ phase }) {
  const { t } = useLanguage();
  const isThinking = phase === "thinking";

  return (
    <div className="chat-message assistant">
      <span className="chat-avatar">
        <i className="fa-solid fa-leaf" />
      </span>
      <div className="chat-bubble typing-bubble voice-processing-bubble">
        <i className={`fa-solid ${isThinking ? "fa-brain" : "fa-microphone"} voice-processing-icon`} />
        <span className="voice-processing-label">
          {isThinking ? t("voiceProcessing.thinking") : t("voiceProcessing.listening")}
        </span>
        <span className="typing-dot" />
        <span className="typing-dot" />
        <span className="typing-dot" />
      </div>
    </div>
  );
}
