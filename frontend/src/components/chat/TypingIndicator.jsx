export default function TypingIndicator() {
  return (
    <div className="chat-message assistant">
      <span className="chat-avatar">
        <i className="fa-solid fa-leaf" />
      </span>
      <div className="chat-bubble typing-bubble">
        <span className="typing-dot" />
        <span className="typing-dot" />
        <span className="typing-dot" />
      </div>
    </div>
  );
}
