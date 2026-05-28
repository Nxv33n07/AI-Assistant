"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, Info, Bot, ChevronDown } from "lucide-react";
import ScriptureCard from "./ScriptureCard";
import type { ChatMessage } from "@/lib/types";

function ThinkingBlock({ thinking }: { thinking: string }) {
  const [open, setOpen] = useState(false);
  return (
    <motion.div
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full rounded-xl border border-white/[0.07] bg-white/[0.03] overflow-hidden mb-1"
    >
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-white/[0.04] transition-colors"
      >
        <motion.span
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="text-white/30"
        >
          <ChevronDown size={13} />
        </motion.span>
        <span className="text-[11px] text-white/35 tracking-wide font-medium italic">
          Thinking…
        </span>
        {!open && (
          <span className="text-[10px] text-white/20 truncate flex-1">
            {thinking.split("\n")[0].slice(0, 60)}…
          </span>
        )}
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            key="thinking-body"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-3 pt-1 border-t border-white/[0.05]">
              <p className="text-[11px] leading-relaxed text-white/30 italic whitespace-pre-wrap font-mono">
                {thinking}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

interface Props {
  message: ChatMessage;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 16, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.38, ease: [0.16, 1, 0.3, 1] }}
      className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}
    >
      {/* Avatar */}
      {isUser ? (
        <div className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center bg-gradient-to-br from-[#c9a84c] to-[#e8c86a] text-[#0a0f1e] font-bold text-xs shadow-lg shadow-[#c9a84c]/20">
          You
        </div>
      ) : (
        <motion.div
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.05, type: "spring", stiffness: 300 }}
          className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center
                     bg-gradient-to-br from-[#0d1829] to-[#162240] border border-[#c9a84c]/40
                     shadow-lg shadow-[#c9a84c]/10"
        >
          <Bot size={14} className="text-[#c9a84c]" />
        </motion.div>
      )}

      <div
        className={`max-w-[80%] flex flex-col gap-1.5 ${isUser ? "items-end" : "items-start"}`}
      >
        {/* Safety banner */}
        {message.safety_flag && (
          <motion.div
            initial={{ opacity: 0, x: isUser ? 8 : -8 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-start gap-2 rounded-xl bg-amber-950/60 border border-amber-500/25
                       backdrop-blur-sm px-3 py-2 text-amber-300 text-xs w-full"
          >
            <AlertTriangle size={12} className="mt-0.5 flex-shrink-0" />
            <span>
              <strong className="uppercase tracking-widest text-[10px]">
                {message.safety_flag.severity === "blocked" ? "Policy" : "Note"}
              </strong>{" "}
              · {message.safety_flag.category.replace(/_/g, " ")}
            </span>
          </motion.div>
        )}

        {/* Corrections */}
        {message.corrections && message.corrections.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="flex items-start gap-2 rounded-xl bg-sky-950/60 border border-sky-500/25
                       backdrop-blur-sm px-3 py-2 text-sky-300 text-xs w-full"
          >
            <Info size={12} className="mt-0.5 flex-shrink-0" />
            <div className="flex flex-col gap-0.5">
              {message.corrections.map((c, i) => (
                <span key={i}>{c}</span>
              ))}
            </div>
          </motion.div>
        )}

        {/* Thinking block */}
        {!isUser && message.thinking && (
          <ThinkingBlock thinking={message.thinking} />
        )}

        {/* Bubble */}
        {isUser ? (
          <div
            className="relative rounded-2xl rounded-tr-sm px-4 py-3 text-sm leading-relaxed
                          bg-gradient-to-br from-[#c9a84c] to-[#e8c86a] text-[#0a0f1e] font-medium
                          shadow-lg shadow-[#c9a84c]/20"
          >
            {message.content}
          </div>
        ) : (
          <div
            className="relative rounded-2xl rounded-tl-sm px-4 py-3 text-sm leading-relaxed
                          bg-white/[0.05] backdrop-blur-sm border border-white/[0.08] text-white/90
                          shadow-lg shadow-black/30"
          >
            {/* subtle top glow */}
            <div className="absolute top-0 left-4 right-4 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
            {message.content}
          </div>
        )}

        {/* Scripture cards */}
        {!isUser &&
          message.scripture_references &&
          message.scripture_references.length > 0 && (
            <div className="w-full flex flex-col">
              {message.scripture_references.map((ref, i) => (
                <ScriptureCard key={i} verse={ref} index={i} />
              ))}
            </div>
          )}

        <span
          suppressHydrationWarning
          className="text-white/20 text-[9px] px-1 select-none"
        >
          {message.timestamp.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>
    </motion.div>
  );
}
