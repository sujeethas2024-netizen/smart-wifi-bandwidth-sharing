import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FiCheckCircle, FiCpu, FiZap } from "react-icons/fi";
import "../styles/components.css";

const STAGES = [
  { label: "Calculating demand matrix…", icon: <FiZap />, duration: 1400 },
  { label: "Applying Game Theory (Nash Equilibrium)…", icon: <FiCpu />, duration: 1800 },
  { label: "Optimizing fairness weights…", icon: <FiCpu />, duration: 1200 },
];

/**
 * Full-screen animated allocation sequence:
 *   Calculating… ████████░░ → Applying Game Theory… → Completed ✔
 */
export default function AllocationAnimation({ open, onComplete }) {
  const [stage, setStage] = useState(0);
  const [progress, setProgress] = useState(0);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!open) {
      setStage(0);
      setProgress(0);
      setDone(false);
      return;
    }

    let cancelled = false;
    let stageIdx = 0;

    const runStage = () => {
      if (cancelled || stageIdx >= STAGES.length) {
        setDone(true);
        setTimeout(() => !cancelled && onComplete?.(), 1300);
        return;
      }
      setStage(stageIdx);
      const dur = STAGES[stageIdx].duration;
      const start = performance.now();

      const tick = (now) => {
        if (cancelled) return;
        const t = Math.min(1, (now - start) / dur);
        // overall progress across all stages
        const overall =
          ((stageIdx + t) / STAGES.length) * 100;
        setProgress(Math.round(overall));
        if (t < 1) requestAnimationFrame(tick);
        else {
          stageIdx += 1;
          runStage();
        }
      };
      requestAnimationFrame(tick);
    };

    runStage();
    return () => {
      cancelled = true;
    };
  }, [open]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="alloc-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div
            className="alloc-modal glass"
            initial={{ scale: 0.85, y: 30, opacity: 0 }}
            animate={{ scale: 1, y: 0, opacity: 1 }}
            exit={{ scale: 0.9, y: 20, opacity: 0 }}
            transition={{ type: "spring", stiffness: 260, damping: 22 }}
          >
            {!done ? (
              <>
                <div className="alloc-spinner">
                  <span />
                  <span />
                  <span />
                </div>

                <AnimatePresence mode="wait">
                  <motion.h3
                    key={stage}
                    initial={{ opacity: 0, y: 14 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -14 }}
                    transition={{ duration: 0.25 }}
                    className="alloc-stage"
                  >
                    {STAGES[stage].icon} {STAGES[stage].label}
                  </motion.h3>
                </AnimatePresence>

                <div className="alloc-bar">
                  <motion.div
                    className="alloc-fill"
                    animate={{ width: `${progress}%` }}
                    transition={{ ease: "linear", duration: 0.15 }}
                  />
                </div>
                <p className="alloc-pct mono">{progress}%</p>
              </>
            ) : (
              <motion.div
                className="alloc-done"
                initial={{ scale: 0.6, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ type: "spring", stiffness: 300, damping: 15 }}
              >
                <motion.span
                  className="done-icon"
                  initial={{ rotate: -30 }}
                  animate={{ rotate: 0 }}
                >
                  <FiCheckCircle />
                </motion.span>
                <h3>Allocation Completed ✔</h3>
                <p>Bandwidth redistributed fairly across all devices.</p>
              </motion.div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}