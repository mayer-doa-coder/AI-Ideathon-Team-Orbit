import { useRef, useState } from "react";
import { useLanguage } from "../../context/LanguageContext";
import { blobToWavBlob } from "../../utils/audioToWav";

const MAX_IMAGE_BYTES = 8 * 1024 * 1024; // crop.health caps images well under this; fail fast client-side
// MediaRecorder never offers "audio/wav" directly — pick whichever
// container the browser actually supports; blobToWavBlob re-encodes it to
// real WAV afterwards regardless of which of these was used.
const RECORDER_MIME_CANDIDATES = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4"];

function pickRecorderMimeType() {
  if (typeof MediaRecorder === "undefined" || !MediaRecorder.isTypeSupported) return "";
  return RECORDER_MIME_CANDIDATES.find((type) => MediaRecorder.isTypeSupported(type)) || "";
}

export default function ChatInput({
  onSend,
  disabled,
  placeholder = null,
  onShareLocation,
  locationStatus = "idle", // "idle" | "granted" | "denied"
}) {
  const { t } = useLanguage();
  const [value, setValue] = useState("");
  const [image, setImage] = useState(null); // { file, previewUrl } | null
  const [imageError, setImageError] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessingVoice, setIsProcessingVoice] = useState(false);
  const [voiceError, setVoiceError] = useState(null);
  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  function handlePickImage(e) {
    const file = e.target.files?.[0];
    e.target.value = ""; // allow picking the same file again later
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      setImageError(t("chatInput.imageTypeError"));
      return;
    }
    if (file.size > MAX_IMAGE_BYTES) {
      setImageError(t("chatInput.imageSizeError"));
      return;
    }

    setImageError(null);
    setImage((prev) => {
      if (prev) URL.revokeObjectURL(prev.previewUrl);
      return { file, previewUrl: URL.createObjectURL(file) };
    });
  }

  function clearImage() {
    setImage((prev) => {
      if (prev) URL.revokeObjectURL(prev.previewUrl);
      return null;
    });
  }

  // Tap-to-start / tap-to-stop, not press-and-hold — stopping immediately
  // sends the recording (same mechanism as an image attachment: base64 in
  // the same POST /api/chat body, see services/chatApi.js), rather than
  // leaving a third "now press send" step.
  async function startRecording() {
    setVoiceError(null);
    if (typeof MediaRecorder === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      setVoiceError(t("chatInput.voiceUnsupported"));
      return;
    }
    let stream;
    try {
      // Explicit constraints, not bare `{ audio: true }` — the shorthand
      // leaves echo cancellation / noise suppression / auto-gain up to each
      // browser's own default, and not every browser turns them all on for
      // it, which was making transcription struggle on real recordings.
      stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
    } catch {
      setVoiceError(t("chatInput.micDenied"));
      return;
    }

    const mimeType = pickRecorderMimeType();
    const recorderOptions = { audioBitsPerSecond: 128000, ...(mimeType ? { mimeType } : {}) };
    const recorder = new MediaRecorder(stream, recorderOptions);
    audioChunksRef.current = [];

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunksRef.current.push(e.data);
    };

    recorder.onstop = async () => {
      stream.getTracks().forEach((track) => track.stop());
      const rawBlob = new Blob(audioChunksRef.current, { type: recorder.mimeType || "audio/webm" });
      audioChunksRef.current = [];

      setIsProcessingVoice(true);
      try {
        const wavBlob = await blobToWavBlob(rawBlob);
        onSend(t("chatInput.voicePlaceholderText"), null, wavBlob);
      } catch {
        setVoiceError(t("chatInput.voiceProcessError"));
      } finally {
        setIsProcessingVoice(false);
      }
    };

    recorder.start();
    mediaRecorderRef.current = recorder;
    setIsRecording(true);
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
    mediaRecorderRef.current = null;
    setIsRecording(false);
  }

  function resizeTextarea(el) {
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }

  function handleSubmit(e) {
    e.preventDefault();
    const trimmed = value.trim();
    if ((!trimmed && !image) || disabled) return;
    onSend(trimmed || t("chatInput.imageDefaultCaption"), image?.file ?? null);
    setValue("");
    clearImage();
    resizeTextarea(textareaRef.current);
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setImageError(t("chatInput.imageDropError"));
      return;
    }
    setImageError(null);
    setImage((prev) => {
      if (prev) URL.revokeObjectURL(prev.previewUrl);
      return { file, previewUrl: URL.createObjectURL(file) };
    });
  }

  const locationTitle =
    locationStatus === "granted"
      ? t("chatInput.locationGranted")
      : locationStatus === "denied"
        ? t("chatInput.locationDenied")
        : t("chatInput.locationIdle");

  return (
    <form
      className="chat-input-form"
      onSubmit={handleSubmit}
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
    >
      {image && (
        <div className="chat-image-preview">
          <img src={image.previewUrl} alt={t("chatInput.photoPreviewAlt")} />
          <button
            type="button"
            className="chat-image-preview-remove"
            aria-label={t("chatInput.removePhotoLabel")}
            onClick={clearImage}
          >
            <i className="fa-solid fa-xmark" />
          </button>
        </div>
      )}
      {imageError && <p className="chat-image-error">{imageError}</p>}
      {voiceError && <p className="chat-image-error">{voiceError}</p>}
      {isRecording && (
        <div className="chat-recording-indicator">
          <span className="recording-dot" /> {t("chatInput.recordingStatus")}
        </div>
      )}
      {isProcessingVoice && <div className="chat-recording-indicator">{t("chatInput.processingVoice")}</div>}

      <div className="chat-input-bar">
        <button
          type="button"
          className="chat-icon-btn"
          aria-label={t("chatInput.voiceUnavailableAria")}
          title={t("chatInput.voiceUnavailableTitle")}
          disabled
        >
          <i className="fa-solid fa-microphone" />
        </button>
        <button
          type="button"
          className={`chat-icon-btn${image ? " chat-icon-btn-active" : ""}`}
          aria-label={t("chatInput.attachPhotoLabel")}
          title={t("chatInput.attachPhotoLabel")}
          onClick={() => fileInputRef.current?.click()}
        >
          <i className="fa-solid fa-camera" />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handlePickImage}
          style={{ display: "none" }}
        />
        <button
          type="button"
          className={`chat-icon-btn${locationStatus === "granted" ? " chat-icon-btn-active" : ""}`}
          aria-label={locationTitle}
          title={locationTitle}
          onClick={onShareLocation}
        >
          <i className="fa-solid fa-location-crosshairs" />
        </button>
        <textarea
          ref={textareaRef}
          rows={1}
          placeholder={image ? t("chatInput.photoNotePlaceholder") : placeholder ?? t("chatInput.defaultPlaceholder")}
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            resizeTextarea(e.target);
          }}
          onKeyDown={handleKeyDown}
          disabled={disabled}
        />
        <button
          type="submit"
          className="chat-send-btn"
          aria-label={t("chatInput.sendLabel")}
          disabled={disabled || (!value.trim() && !image)}
        >
          <i className="fa-solid fa-paper-plane" />
        </button>
      </div>
    </form>
  );
}
