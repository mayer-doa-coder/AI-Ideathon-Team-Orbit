import { useEffect, useRef, useState } from "react";

export default function Counter({ value, suffix = "", duration = 1500 }) {
  const [display, setDisplay] = useState(0);
  const ref = useRef(null);
  const hasRun = useRef(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasRun.current) {
          hasRun.current = true;
          const start = performance.now();

          function tick(now) {
            const progress = Math.min((now - start) / duration, 1);
            setDisplay(Math.round(progress * value));
            if (progress < 1) requestAnimationFrame(tick);
          }

          requestAnimationFrame(tick);
        }
      },
      { threshold: 0.4 }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [value, duration]);

  return (
    <span ref={ref}>
      {display}
      {suffix}
    </span>
  );
}
