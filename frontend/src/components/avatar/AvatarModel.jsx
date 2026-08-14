import { useEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { useAnimations, useFBX } from "@react-three/drei";
import * as THREE from "three";

export const MODEL_URL = "/assets/models/Dodging Right.fbx";

// Target standing height in scene units (treated as meters) — the model is
// auto-scaled to this from its measured bounding box rather than a
// hardcoded factor, since Mixamo FBX unit conventions vary. Also re-grounds
// the feet at y=0 and centers on x/z, so camera framing in Avatar3D doesn't
// have to guess at the source file's raw scale.
const TARGET_HEIGHT = 1.7;

// Mixamo always names the exported animation clip "mixamo.com" regardless
// of which action was picked on their site — this file's one clip is a
// "Dodging Right" action (see the source filename), not a resting pose, so
// it's deliberately never autoplayed (see the empty-idle branch below). If
// a future export includes a real idle loop, name it something containing
// "idle" and it'll be picked up automatically with no code changes.
function findIdleClipName(names) {
  return names.find((n) => /idle/i.test(n)) ?? null;
}

// Checked in case a future model swap has a usable mouth control — this
// export has neither (see the AvatarModel doc comment below and the
// integration report). Covers common Mixamo/ARKit/generic naming so a
// replacement FBX/GLB works without touching this component.
const MOUTH_MORPH_CANDIDATES = ["mouthOpen", "MouthOpen", "jawOpen", "JawOpen", "viseme_aa", "mouth_open"];
const JAW_BONE_PATTERN = /jaw/i;

function findMouthControl(root) {
  let morphMesh = null;
  let morphIndex = -1;
  let jawBone = null;

  root.traverse((obj) => {
    if (!morphMesh && obj.morphTargetDictionary) {
      const key = MOUTH_MORPH_CANDIDATES.find((name) => name in obj.morphTargetDictionary);
      if (key) {
        morphMesh = obj;
        morphIndex = obj.morphTargetDictionary[key];
      }
    }
    if (!jawBone && obj.isBone && JAW_BONE_PATTERN.test(obj.name)) {
      jawBone = obj;
    }
  });

  return { morphMesh, morphIndex, jawBone };
}

/**
 * Loads and renders the Mixamo FBX inside a <Canvas>. Handles body/idle
 * animation and (once a suitable rig exists) reactive mouth movement.
 *
 * Current model has no facial morph targets and no jaw bone — confirmed by
 * direct inspection (101 bones, all body/hair/clothing; 4 skinned meshes,
 * zero morph targets on any of them; see the avatar integration report).
 * So `audioLevel`/`isSpeaking` are genuinely smoothed every frame below
 * (real interpolation, not a stub), but there is currently nothing to
 * apply the result to — no fake head-bob or scale hack is used as a
 * substitute. This will start working automatically the moment a model
 * with a mouth morph target or jaw bone is swapped in.
 */
export default function AvatarModel({ audioLevel = 0, isSpeaking = false, onReady }) {
  const group = useRef();
  const fbx = useFBX(MODEL_URL);
  const { actions, names } = useAnimations(fbx.animations, group);

  // useFBX suspends until the model resolves, so this component's body only
  // ever runs once the model is actually ready — telling Avatar3D that lets
  // it cancel its loading-timeout fallback instead of racing it.
  useEffect(() => {
    onReady?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const box = new THREE.Box3().setFromObject(fbx);
    const size = box.getSize(new THREE.Vector3());
    const scale = TARGET_HEIGHT / (size.y || 1);
    fbx.scale.setScalar(scale);

    const groundedBox = new THREE.Box3().setFromObject(fbx);
    fbx.position.x -= (groundedBox.max.x + groundedBox.min.x) / 2;
    fbx.position.z -= (groundedBox.max.z + groundedBox.min.z) / 2;
    fbx.position.y -= groundedBox.min.y;
  }, [fbx]);

  useEffect(() => {
    const idleName = findIdleClipName(names);
    if (!idleName) {
      if (import.meta.env.DEV) {
        console.info(
          `[Avatar3D] No idle animation clip in this FBX (found: ${names.join(", ") || "none"}) — ` +
            "holding the rig's bind pose instead of looping a non-idle action."
        );
      }
      return undefined;
    }
    const action = actions[idleName]?.reset().fadeIn(0.3).play();
    return () => action?.fadeOut(0.2);
  }, [actions, names]);

  const mouthControl = useMemo(() => {
    const control = findMouthControl(fbx);
    if (import.meta.env.DEV && !control.morphMesh && !control.jawBone) {
      console.info(
        "[Avatar3D] No mouth morph target or jaw bone found on this model — reactive lip sync has " +
          "nothing to drive yet. Body rendering is unaffected; see the avatar integration report."
      );
    }
    return control;
  }, [fbx]);

  const currentMouthOpen = useRef(0);

  useFrame((_, delta) => {
    const target = isSpeaking ? audioLevel : 0;
    // Frame-rate-independent exponential smoothing, so mouth movement eases
    // toward the target instead of jumping — genuinely computed every
    // frame regardless of whether there's a rig to apply it to (see above).
    const smoothing = 1 - Math.pow(0.001, delta);
    currentMouthOpen.current += (target - currentMouthOpen.current) * smoothing;

    const { morphMesh, morphIndex, jawBone } = mouthControl;
    if (morphMesh && morphIndex >= 0) {
      morphMesh.morphTargetInfluences[morphIndex] = currentMouthOpen.current;
    } else if (jawBone) {
      jawBone.rotation.x = currentMouthOpen.current * 0.25;
    }
  });

  return <primitive ref={group} object={fbx} />;
}
