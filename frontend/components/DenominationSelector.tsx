"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Check } from "lucide-react";
import { Denomination, DENOMINATION_LABELS } from "@/lib/types";

interface Props {
  value: Denomination;
  onChange: (d: Denomination) => void;
}

const DENOMINATION_ICONS: Record<Denomination, string> = {
  nondenominational: "✝",
  catholic: "⛪",
  protestant_reformed: "📖",
  protestant_evangelical: "🕊",
  protestant_lutheran: "🪷",
  orthodox_eastern: "☦",
  pentecostal: "🔥",
};

export default function DenominationSelector({ value, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node))
        setOpen(false);
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const options = Object.keys(DENOMINATION_LABELS) as Denomination[];

  return (
    <div ref={ref} className="relative">
      <motion.button
        onClick={() => setOpen((o) => !o)}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.97 }}
        className="flex items-center gap-2 bg-white/[0.06] hover:bg-white/[0.1] border border-[#c9a84c]/30 hover:border-[#c9a84c]/60 text-[#c9a84c] text-sm rounded-xl px-3 py-2 transition-colors"
      >
        <span className="text-base leading-none">
          {DENOMINATION_ICONS[value]}
        </span>
        <span className="hidden sm:block max-w-[140px] truncate">
          {DENOMINATION_LABELS[value]}
        </span>
        <motion.span
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronDown size={13} />
        </motion.span>
      </motion.button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.96 }}
            transition={{ duration: 0.15, ease: "easeOut" }}
            className="absolute right-0 top-full mt-2 w-56 rounded-2xl overflow-hidden z-[200]
                       bg-[#0d1829]/95 backdrop-blur-xl border border-white/10 shadow-2xl shadow-black/60"
          >
            {options.map((d, i) => (
              <motion.button
                key={d}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.03 }}
                onClick={() => {
                  onChange(d);
                  setOpen(false);
                }}
                className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm text-left transition-colors
                  ${
                    d === value
                      ? "bg-[#c9a84c]/15 text-[#c9a84c]"
                      : "text-white/70 hover:bg-white/[0.06] hover:text-white"
                  }`}
              >
                <span className="text-base w-5 text-center">
                  {DENOMINATION_ICONS[d]}
                </span>
                <span className="flex-1">{DENOMINATION_LABELS[d]}</span>
                {d === value && <Check size={13} className="text-[#c9a84c]" />}
              </motion.button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
