import { Suspense, useEffect, useState } from "react";
import { Canvas } from "@react-three/fiber";
import AvatarErrorBoundary from "./AvatarErrorBoundary";
import AvatarModel from "./AvatarModel";

// How long to wait for the 3D model before giving up and showing the
// fallback instead. AvatarErrorBoundary only catches thrown errors — a
// model that's stuck mid-load (slow fetch, silently failed WebGL context,
// or anything else that doesn't throw) leaves <Suspense fallback={null}>
// showing nothing indefinitely, which reads as a blank/transparent box
// sitting over the chat rather than an actual avatar. This makes "still
// loading" and "never going to load" look the same to the farmer: the
// intentional leaf-icon fallback, not empty space.
const LOAD_TIMEOUT_MS = 6000;

/**
 * The Agrisense AI assistant's 3D avatar — renders the Mixamo character
 * with a calm idle presence next to the chat conversation.
 *
 * `isSpeaking`/`audioLevel` are accepted now so a future TTS/Web Audio
 * integration can plug in without changing this component's API:
 *
 *   Web Audio analyser -> audioLevel (0..1) -> <Avatar3D audioLevel={...} isSpeaking />
 *
 * This component only renders the avatar and reacts to that state — it
 * never generates or analyzes audio itself (kept out of scope on purpose,
 * see the avatar integration report). Both props default to the silent/
 * neutral state, so nothing here fabricates speech before real voice
 * integration exists.
 */
export default function Avatar3D({ isSpeaking = false, audioLevel = 0, className = "" }) {
  const [loaded, setLoaded] = useState(false);
  const [timedOut, setTimedOut] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setTimedOut(true), LOAD_TIMEOUT_MS);
    return () => clearTimeout(timer);
  }, []);

  const showFallback = timedOut && !loaded;

  return (
    <div className={`avatar3d-canvas ${className}`.trim()}>
      {showFallback ? (
        <AvatarFallback />
      ) : (
        <AvatarErrorBoundary fallback={<AvatarFallback />}>
          <Canvas
            camera={{ position: [0, 1.4, 1.6], fov: 28 }}
            dpr={[1, 1.5]}
            gl={{ alpha: true, antialias: true }}
          >
            <ambientLight intensity={0.8} />
            <directionalLight position={[2, 4, 3]} intensity={1.1} />
            <directionalLight position={[-2, 2, -2]} intensity={0.35} color="#bfe3c9" />
            <Suspense fallback={null}>
              <AvatarModel audioLevel={audioLevel} isSpeaking={isSpeaking} onReady={() => setLoaded(true)} />
            </Suspense>
          </Canvas>
        </AvatarErrorBoundary>
      )}
    </div>
  );
}

function AvatarFallback() {
  return (
    <div className="avatar3d-fallback">
      <i className="fa-solid fa-leaf" />
    </div>
  );
}
