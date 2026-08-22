import { useEffect, useRef, useState } from "react";

/**
 * Animated number that counts up from 0 (or previous value) to `value`
 * whenever `value` changes. Uses requestAnimationFrame for smoothness.
 */
export default function CountUp({
  value = 0,
  duration = 1200,
  decimals = 0,
  suffix = "",
  prefix = "",
}) {
  const [display, setDisplay] = useState(0);
  const prevRef = useRef(0);
  const frameRef = useRef(null);

  useEffect(() => {
    const from = prevRef.current;
    const to = Number(value) || 0;
    const start = performance.now();

    const step = (now) => {
      const t = Math.min(1, (now - start) / duration);
      // easeOutCubic
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(from + (to - from) * eased);
      if (t < 1) {
        frameRef.current = requestAnimationFrame(step);
      } else {
        prevRef.current = to;
      }
    };

    frameRef.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frameRef.current);
  }, [value, duration]);

  return (
    <span>
      {prefix}
      {display.toFixed(decimals)}
      {suffix}
    </span>
  );
}