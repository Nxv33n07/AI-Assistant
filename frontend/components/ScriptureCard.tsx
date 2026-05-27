"use client";

import { motion } from "framer-motion";
import { BookOpen, Sparkles } from "lucide-react";
import type { ScriptureRef } from "@/lib/types";

interface Props {
  verse: ScriptureRef;
  index?: number;
}

export default function ScriptureCard({ verse, index = 0 }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        duration: 0.4,
        delay: index * 0.08,
        ease: [0.16, 1, 0.3, 1],
      }}
      className="relative overflow-hidden rounded-xl border border-[#c9a84c]/25 bg-gradient-to-br from-[#0d1829] to-[#080f1e] px-4 py-3 mt-2 group"
    >
      {/* Shimmer overlay */}
      <motion.div
        className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
        style={{
          background:
            "linear-gradient(105deg, transparent 30%, rgba(201,168,76,0.06) 50%, transparent 70%)",
        }}
      />

      {/* Gold top-edge glow */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#c9a84c]/50 to-transparent" />

      {/* Header row */}
      <div className="flex items-center gap-2 mb-1.5">
        {verse.relevance === "direct" ? (
          <BookOpen size={12} className="text-[#c9a84c]" />
        ) : (
          <Sparkles size={12} className="text-[#c9a84c]/70" />
        )}
        <span className="font-semibold text-[#c9a84c] text-xs tracking-wider uppercase">
          {verse.reference}
        </span>
        <span className="text-[#c9a84c]/40 text-[10px]">
          ({verse.translation})
        </span>
        {verse.relevance === "semantic" && (
          <span className="ml-auto text-[9px] uppercase tracking-widest text-white/20 border border-white/10 rounded px-1.5 py-0.5">
            related
          </span>
        )}
      </div>

      {/* Verse text */}
      <p className="text-white/75 text-sm italic leading-relaxed">
        <span className="text-[#c9a84c]/60 text-lg leading-none mr-0.5">
          &ldquo;
        </span>
        {verse.text}
        <span className="text-[#c9a84c]/60 text-lg leading-none ml-0.5">
          &rdquo;
        </span>
      </p>
    </motion.div>
  );
}
