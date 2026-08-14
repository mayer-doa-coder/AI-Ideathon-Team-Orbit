import { useEffect, useState } from "react";

/**
 * Agriva's #agri-preloader, ported to React.
 *
 * The template hides this from a `window.load` listener inside main.js. We
 * inject main.js after React has painted (see utils/agrivaTemplate.js), by
 * which point `load` has almost always already fired — so that listener never
 * runs and the original markup would sit over the page forever. The fade is
 * therefore driven from here instead, on the same 500ms/0.15s timing the
 * template uses.
 */
export default function Preloader() {
  const [hidden, setHidden] = useState(false);
  const [removed, setRemoved] = useState(false);

  useEffect(() => {
    const fade = setTimeout(() => setHidden(true), 500);
    const strip = setTimeout(() => setRemoved(true), 650);
    return () => {
      clearTimeout(fade);
      clearTimeout(strip);
    };
  }, []);

  if (removed) return null;

  return (
    <div
      id="agri-preloader"
      style={{
        transition: "opacity 0.15s ease",
        opacity: hidden ? 0 : 1,
      }}
    >
      <div className="preloader-content">
        <img src="/assets/img/leaf.png" alt="" className="farmer-loader" />
        <h4>Loading Green Leaf...</h4>
      </div>
    </div>
  );
}
