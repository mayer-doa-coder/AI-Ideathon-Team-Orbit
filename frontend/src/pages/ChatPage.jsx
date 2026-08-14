import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import ChatHeader from "../components/chat/ChatHeader";
import ChatMessage from "../components/chat/ChatMessage";
import TypingIndicator from "../components/chat/TypingIndicator";
import VoiceProcessingIndicator from "../components/chat/VoiceProcessingIndicator";
import ChatInput from "../components/chat/ChatInput";
// import Avatar3D from "../components/avatar/Avatar3D"; // temporarily disabled
import FarmProfileStrip from "../components/dashboard/FarmProfileStrip";
import TraceLog from "../components/dashboard/TraceLog";
import WeatherWidget from "../components/dashboard/WeatherWidget";
import MarketPriceCard from "../components/dashboard/MarketPriceCard";
import CropComparison from "../components/dashboard/CropComparison";
import SeasonPlanTimeline from "../components/dashboard/SeasonPlanTimeline";
import FinancialBreakdown from "../components/dashboard/FinancialBreakdown";
import AlertsFeed from "../components/dashboard/AlertsFeed";
import KnowledgeSources from "../components/dashboard/KnowledgeSources";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { fetchChatState, streamChatMessage } from "../services/chatApi";
import { checkWeatherNow, getMyFarm, getMyPlan, listAlerts, simulateTrigger } from "../services/monitorApi";
import { getSupportedCrops } from "../services/marketApi";
import { serializeSeasonPlan } from "../utils/serializeSeasonPlan";
import { tf as tfPlain } from "../i18n/translations";
import "../styles/dashboard.css";
import "../styles/avatar.css";

// Adapts the monitor API's ForecastResult ({daily: [{date, rainfall_mm, ...}]})
// into WeatherWidget's flat `weather` prop shape (the same shape the
// conversation graph's own `weather` chat event already uses).
function adaptRealWeather(weatherData, location) {
  if (!weatherData?.daily?.length) return null;
  const days = weatherData.daily;
  const rainfall = days.map((d) => d.rainfall_mm);
  const temps = days.flatMap((d) => [d.temp_min_c, d.temp_max_c]);
  const heavyIndex = rainfall.findIndex((mm) => mm >= 30);

  return {
    location,
    dates: days.map((d) => d.date),
    daily_rainfall_mm: rainfall,
    temp_range_c: `${Math.round(Math.min(...temps))}-${Math.round(Math.max(...temps))}`,
    heavy_rain_date: heavyIndex >= 0 ? days[heavyIndex].date : null,
    alert:
      heavyIndex >= 0
        ? tfPlain("chatPage.heavyRainAlertTemplate", { mm: rainfall[heavyIndex], date: days[heavyIndex].date })
        : null,
  };
}

function adaptRealAlerts(rows) {
  return rows.map((row) => ({
    id: row.id,
    type: "warning",
    date: new Date(row.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
    text: row.message,
  }));
}

let nextId = Date.now();

// Backend farm_profile keys (location, acres, soil_type, water_availability,
// budget, season) don't match FarmProfileStrip's onboardingSteps-driven keys
// (location, acreage, soilType, water, budget, season) — translate rather
// than touch the shared strip component. Used for both `farmProfile` (from
// the conversation graph) and `realFarm` (from the monitor agent) — both
// are already in the backend's key shape.
function mapProfileForStrip(profile) {
  if (!profile) return {};
  return {
    location: profile.location || null,
    acreage: profile.acres != null ? tfPlain("farmProfileStrip.acresValueTemplate", { acres: profile.acres }) : null,
    soilType: profile.soil_type || null,
    water: profile.water_availability || null,
    budget: profile.budget != null ? `৳${profile.budget.toLocaleString()}` : null,
    season: profile.season || null,
  };
}

function cropIdFromName(name) {
  return name ? name.toLowerCase().replace(/\s+/g, "-") : null;
}

export default function ChatPage() {
  const { username, token, logout } = useAuth();
  const { t, tf, language } = useLanguage();
  const navigate = useNavigate();

  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);

  const [messages, setMessages] = useState([]);
  const [farmProfile, setFarmProfile] = useState({});
  const [traceEntries, setTraceEntries] = useState([]);
  const [crops, setCrops] = useState([]);
  const [selectedCropId, setSelectedCropId] = useState(null);
  const [weather, setWeather] = useState(null);
  const [seasonPlan, setSeasonPlan] = useState(null);
  const [financials, setFinancials] = useState(null);
  // The figures this plan replaced, so the breakdown can show a before/after
  // when a re-plan, scenario or monitor adjustment changes the numbers. Null
  // whenever the current figures are the first ones this session — there is
  // nothing to compare against on a freshly loaded plan.
  const [previousFinancials, setPreviousFinancials] = useState(null);
  // setFinancials' updater cannot be used to read the old value here: these
  // calls happen inside async stream/fetch callbacks where the captured
  // `financials` is stale, and triggering a second setState from inside an
  // updater fires twice under StrictMode.
  const financialsRef = useRef(null);
  const [sources, setSources] = useState([]);
  const [marketCrops, setMarketCrops] = useState(["rice"]);

  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState("");

  // True only while the in-flight turn started as a recorded voice message
  // (see ChatInput's mic button) — swaps the loading indicator from the
  // normal three-dot TypingIndicator to VoiceProcessingIndicator's
  // "listening" -> "thinking" phases.
  const [isVoiceTurn, setIsVoiceTurn] = useState(false);
  const [voicePhase, setVoicePhase] = useState("listening"); // "listening" | "thinking"

  // Farmer's current browser position, opt-in — for "urea near my area"
  // style marketplace queries. Kept separate from farmProfile: where the
  // farmer is chatting from and where their farm is registered aren't the
  // same thing, and the backend already treats them as distinct signals
  // (see ChatRequest.lat/lon vs farm_profile.lat/lon).
  const [location, setLocation] = useState(null);
  const [locationStatus, setLocationStatus] = useState("idle"); // "idle" | "granted" | "denied"

  const scrollRef = useRef(null);

  function handleShareLocation() {
    if (!navigator.geolocation) {
      setLocationStatus("denied");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({ lat: position.coords.latitude, lon: position.coords.longitude });
        setLocationStatus("granted");
      },
      () => setLocationStatus("denied"),
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 }
    );
  }

  // The monitor agent is real end to end, but only once a farm + committed
  // season plan actually exist in Postgres for this account — which today
  // means the conversation agent's onboarding has run, or (for testing/demo)
  // `scripts/seed_demo_farm.py` was used. Until then, `realFarm` stays null
  // and the weather/alerts panels fall back to the conversation graph's own
  // (also real) `weather` chat state.
  const [realFarm, setRealFarm] = useState(null);
  const [realWeather, setRealWeather] = useState(null);
  const [realAlerts, setRealAlerts] = useState([]);
  const [checkingWeather, setCheckingWeather] = useState(false);

  function refreshRealAlerts(farmId) {
    listAlerts(token, farmId)
      .then(setRealAlerts)
      .catch(() => {});
  }

  // Hydrate from the real persisted conversation (LangGraph checkpointer,
  // keyed by this user's id) instead of a per-browser localStorage cache —
  // the backend is now the single source of truth for memory.
  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    fetchChatState(token)
      .then((state) => {
        if (cancelled) return;
        setMessages(
          state.messages.length > 0
            ? state.messages
            : [{ id: "greeting", role: "assistant", text: t("chatPage.greeting") }]
        );
        setFarmProfile(state.farm_profile || {});
        setCrops(state.crop_candidates || []);
        setSelectedCropId(cropIdFromName(state.selected_crop));
        setSeasonPlan(
          state.season_plan ? { crop: state.selected_crop, milestones: state.season_plan } : null
        );
        initFinancials(state.financials || null);
        setWeather(state.weather || null);
        setSources(state.sources || []);
        setTraceEntries(state.trace_log || []);
      })
      .catch((err) => !cancelled && setLoadError(err.message))
      .finally(() => !cancelled && setIsLoading(false));

    return () => {
      cancelled = true;
    };
    // t's identity changes every render (see LanguageContext), so including
    // it here would refetch on every render instead of once per token —
    // the greeting text it produces only needs to reflect whatever language
    // is active at the moment this effect actually runs.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  useEffect(() => {
    // Waits for the chat-state hydration above to finish first, so this
    // effect's plan (read straight from Postgres, reflecting any monitor
    // adjustment) always applies *after* — and therefore wins over — the
    // conversation checkpoint's season_plan, regardless of which request
    // happens to resolve first. Without this ordering, a race could leave
    // the stale pre-adjustment plan on screen after a refresh.
    if (!token || isLoading) return;
    let cancelled = false;
    getMyFarm(token)
      .then((farm) => {
        if (cancelled) return;
        setRealFarm(farm);
        if (!farm) return null;
        return getMyPlan(token);
      })
      .then((plan) => {
        if (cancelled || !plan?.season_plan) return;
        setSeasonPlan({
          crop: plan.crop,
          milestones: serializeSeasonPlan(plan.season_plan, plan.financials),
        });
        initFinancials(plan.financials || null);
      })
      .catch(() => {
        if (!cancelled) setRealFarm(null);
      });
    return () => {
      cancelled = true;
    };
  }, [token, isLoading]);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    getSupportedCrops(token)
      .then((result) => {
        if (!cancelled && result.crops?.length) setMarketCrops(result.crops);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [token]);

  // Keyed on the farm's id, not the realFarm object itself — realFarm gets
  // re-fetched (new object reference, same id) after every chat turn below
  // so the alerts panel can appear without a page reload once onboarding
  // commits a farm mid-session. Keying on the whole object would re-run a
  // real monitor sweep on every single message instead of once per farm.
  const realFarmId = realFarm?.id;
  useEffect(() => {
    if (!realFarmId) return;
    let cancelled = false;
    checkWeatherNow(token, realFarmId)
      .then((result) => {
        if (cancelled) return;
        setRealWeather(result.weather_data);
        applyMonitorResult(result);
      })
      .catch(() => {});
    refreshRealAlerts(realFarmId);
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [realFarmId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, isStreaming, streamingText]);

  // Finds the most recent message matching `predicate` and applies `patch`
  // to it — used to update the optimistic voice-message bubble (transcript
  // text) and the latest assistant reply (audio URL) once their respective
  // SSE events land after the bubble already exists.
  function patchLastMessage(predicate, patch) {
    setMessages((prev) => {
      const idxFromEnd = [...prev].reverse().findIndex(predicate);
      if (idxFromEnd === -1) return prev;
      const idx = prev.length - 1 - idxFromEnd;
      const next = [...prev];
      next[idx] = { ...next[idx], ...patch };
      return next;
    });
  }

  // Replaces the figures and remembers what they replaced. Only records a
  // previous set when one already existed and actually differs, so re-running
  // a turn that produces identical numbers does not show a no-op comparison.
  //
  // The null case is the important one. A replan does not go straight from old
  // figures to new: core_change_handler first invalidates the plan, which
  // emits `financials: null`, and the recomputed figures only arrive a turn or
  // two later. So the ref deliberately holds the last NON-null figures and is
  // never cleared by an invalidation — otherwise the comparison the farmer
  // actually wants (before the change vs after it) is lost in between.
  function applyFinancials(next) {
    if (!next) {
      setFinancials(null);
      return;
    }
    const prev = financialsRef.current;
    if (prev && JSON.stringify(prev) !== JSON.stringify(next)) {
      setPreviousFinancials(prev);
    }
    financialsRef.current = next;
    setFinancials(next);
  }

  // Initial load of an already-saved plan: these are the farmer's current
  // numbers, not a change, so any stale comparison is cleared.
  function initFinancials(next) {
    financialsRef.current = next || null;
    setPreviousFinancials(null);
    setFinancials(next);
  }

  function handleSend(text, imageFile = null, audioBlob = null) {
    const trimmed = text.trim();
    if ((!trimmed && !imageFile && !audioBlob) || isStreaming) return;

    setMessages((prev) => [
      ...prev,
      {
        id: `u-${nextId++}`,
        role: "user",
        text: trimmed,
        image: imageFile ? URL.createObjectURL(imageFile) : null,
        isVoice: Boolean(audioBlob),
        pendingTranscript: Boolean(audioBlob),
      },
    ]);
    setIsStreaming(true);
    setStreamingText("");
    setIsVoiceTurn(Boolean(audioBlob));
    setVoicePhase("listening");
    // Cleared up front, not just on a "sources" event: qa_agent only emits
    // that event when this turn's tools actually retrieved something (see
    // schemas/chat.py), so a turn that answers from farm_dashboard or
    // doesn't call any retrieval tool at all sends no event whatsoever —
    // leaving the previous turn's web/KB links on screen unless we reset
    // here regardless of what (if anything) this turn reports.
    setSources([]);

    let liveText = "";

    streamChatMessage(
      token,
      trimmed,
      (event) => {
        switch (event.type) {
          case "profile":
            setFarmProfile(event.farm_profile || {});
            break;
          case "trace":
            setTraceEntries((prev) => [event.entry, ...prev]);
            // Once transcribe_audio's own trace entry lands, the STT leg of
            // a voice turn is done (success or fail) — move the loading
            // indicator from "listening" to "thinking", and, on success,
            // replace the placeholder bubble with what was actually heard
            // (never guessed — see nodes/voice_input.py).
            if (event.entry.type === "voice_input" && event.entry.tool === "transcribe_audio") {
              setVoicePhase("thinking");
              const transcribedText = event.entry.response?.text;
              if (transcribedText) {
                patchLastMessage((m) => m.pendingTranscript, {
                  text: transcribedText,
                  pendingTranscript: false,
                });
              } else {
                patchLastMessage((m) => m.pendingTranscript, {
                  pendingTranscript: false,
                  transcriptFailed: true,
                });
              }
            }
            break;
          case "message":
            setMessages((prev) => [
              ...prev,
              { id: `a-${nextId++}`, role: "assistant", text: event.text, badge: event.badge || null },
            ]);
            break;
          case "token":
            liveText += event.content;
            setStreamingText(liveText);
            break;
          case "crops":
            setCrops(event.crops || []);
            break;
          case "weather":
            setWeather(event.weather || null);
            break;
          case "financials":
            applyFinancials(event.financials || null);
            break;
          case "season_plan":
            // Milestones can legitimately come back null (a core-field
            // change invalidated the prior plan) — wrapping that in a
            // truthy object here would make SeasonPlanTimeline crash on
            // .map(null) instead of just hiding the panel.
            setSeasonPlan(event.milestones ? { crop: event.crop, milestones: event.milestones } : null);
            break;
          case "sources":
            setSources(event.sources || []);
            break;
          case "audio":
            // TTS failing (event.tts_error set, no audio_url) is a silent
            // no-op here on purpose — the text reply already rendered via
            // "message" above, and a missing voice reply shouldn't look
            // like a broken app.
            if (event.audio_url) {
              patchLastMessage((m) => m.role === "assistant", { audioUrl: event.audio_url });
            }
            break;
          case "error":
            setMessages((prev) => [
              ...prev,
              { id: `a-${nextId++}`, role: "assistant", text: tf("chatPage.errorTemplate", { error: event.message }) },
            ]);
            break;
          default:
            break;
        }
      },
      location,
      imageFile,
      audioBlob,
      // Speech-to-text language hint for a voice message; ignored otherwise.
      language
    )
      .catch((err) => {
        setMessages((prev) => [
          ...prev,
          { id: `a-${nextId++}`, role: "assistant", text: tf("chatPage.errorTemplate", { error: err.message }) },
        ]);
      })
      .finally(() => {
        setIsStreaming(false);
        setIsVoiceTurn(false);
        if (liveText) {
          setMessages((prev) => [...prev, { id: `a-${nextId++}`, role: "assistant", text: liveText }]);
        }
        setStreamingText("");
        // Onboarding creates the Farm/Plan rows mid-conversation (via the
        // conversation graph's persist node), not through a button click —
        // refetch so realFarm (and therefore the Alerts panel, which is
        // gated on it) appears as soon as that happens instead of only
        // after a manual page reload.
        getMyFarm(token)
          .then(setRealFarm)
          .catch(() => {});
      });
  }

  // A triggered monitor sweep returns the adjusted plan/financials as raw
  // dicts (updated_plan/updated_financials) — never pre-serialized into the
  // milestones shape SeasonPlanTimeline renders, since that serialization
  // only exists on the conversation graph's chat path. Without this, the
  // season plan panel keeps showing the pre-adjustment schedule after a
  // monitor trigger even though the change was correctly computed and saved.
  function applyMonitorResult(result) {
    if (!result.triggered || !result.updated_plan) return;
    setSeasonPlan({
      crop: result.updated_plan.crop,
      milestones: serializeSeasonPlan(result.updated_plan, result.updated_financials),
    });
    applyFinancials(result.updated_financials || null);
  }

  function handleSimulateCheck() {
    if (!realFarm) return;
    setCheckingWeather(true);
    simulateTrigger(token, realFarm.id)
      .then((result) => {
        refreshRealAlerts(realFarm.id);
        applyMonitorResult(result);
        const note = result.triggered
          ? tf("chatPage.monitorCheckCompleteTemplate", { reason: result.trigger_reason })
          : t("chatPage.monitorCheckCompleteNoChange");
        setMessages((prev) => [...prev, { id: `a-${nextId++}`, role: "assistant", text: note }]);
      })
      .catch((err) => {
        setMessages((prev) => [
          ...prev,
          {
            id: `a-${nextId++}`,
            role: "assistant",
            text: tf("chatPage.monitorCheckFailedTemplate", { error: err.message }),
          },
        ]);
      })
      .finally(() => setCheckingWeather(false));
  }

  function handleSelectCrop(crop) {
    setSelectedCropId(crop.id);
    handleSend(tf("chatPage.illGoWithTemplate", { crop: crop.name }));
  }

  function handleLogout() {
    logout();
    navigate("/login");
  }

  const selectedCrop = crops.find((c) => c.id === selectedCropId);

  return (
    <div className="dashboard-page">
      <ChatHeader username={username} onLogout={handleLogout} />

      <div className="dashboard-split">
        <section className="dashboard-chat">
          <div className="chat-messages" ref={scrollRef}>
            {isLoading ? (
              <ChatMessage role="assistant" text={t("chatPage.loadingProfile")} />
            ) : loadError ? (
              <ChatMessage role="assistant" text={tf("chatPage.loadErrorTemplate", { error: loadError })} />
            ) : (
              <>
                {messages.map((m) => (
                  <ChatMessage
                    key={m.id}
                    role={m.role}
                    text={m.text}
                    image={m.image}
                    badge={m.badge}
                    audioUrl={m.audioUrl}
                    isVoice={m.isVoice}
                    transcriptFailed={m.transcriptFailed}
                  />
                ))}
                {isStreaming && isVoiceTurn && <VoiceProcessingIndicator phase={voicePhase} />}
                {isStreaming && !isVoiceTurn && streamingText && <ChatMessage role="assistant" text={streamingText} />}
                {isStreaming && !isVoiceTurn && !streamingText && <TypingIndicator />}
              </>
            )}
          </div>

          <div className="chat-footer">
            <ChatInput
              onSend={handleSend}
              disabled={isLoading || isStreaming}
              placeholder={t("chatPage.inputPlaceholder")}
              onShareLocation={handleShareLocation}
              locationStatus={locationStatus}
            />
          </div>
        </section>

        <section className="dashboard-panel">
          <FarmProfileStrip profile={mapProfileForStrip(farmProfile)} />
          <TraceLog entries={traceEntries} />
          <WeatherWidget
            weather={
              realFarm && realWeather
                ? adaptRealWeather(realWeather, realFarm.location)
                : weather
            }
            live={Boolean(realFarm && realWeather)}
          />
          <MarketPriceCard
            token={token}
            crops={marketCrops}
            season={farmProfile?.season}
            district={farmProfile?.location}
          />
          <CropComparison crops={crops} selectedCropId={selectedCropId} onSelect={handleSelectCrop} />
          {seasonPlan && (
            <SeasonPlanTimeline cropName={seasonPlan.crop} milestones={seasonPlan.milestones} />
          )}
          {financials && (
            <FinancialBreakdown
              cropName={selectedCrop?.name ?? seasonPlan?.crop}
              financials={financials}
              previous={previousFinancials}
            />
          )}
          {realFarm && (
            <AlertsFeed
              alerts={adaptRealAlerts(realAlerts)}
              onSimulateCheck={handleSimulateCheck}
              live
              checking={checkingWeather}
            />
          )}
          <KnowledgeSources sources={sources} />
        </section>
      </div>
    </div>
  );
}
