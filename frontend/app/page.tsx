"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, ImageIcon } from "lucide-react";
import DenominationSelector from "@/components/DenominationSelector";
import type { Denomination } from "@/lib/types";

// Both components use client-only APIs (uuidv4, Date, Three.js) — skip SSR entirely
const ParticleBackground = dynamic(
  () => import("@/components/ParticleBackground"),
  { ssr: false },
);

const ChatInterface = dynamic(() => import("@/components/ChatInterface"), {
  ssr: false,
});

const ImagePanel = dynamic(() => import("@/components/ImagePanel"), {
  ssr: false,
});

type Tab = "chat" | "image";

const TAB_VARIANTS = {
  enter: (dir: number) => ({ opacity: 0, x: dir * 24, scale: 0.98 }),
  center: { opacity: 1, x: 0, scale: 1 },
  exit: (dir: number) => ({ opacity: 0, x: dir * -24, scale: 0.98 }),
};

export default function Home() {
  const [denomination, setDenomination] =
    useState<Denomination>("nondenominational");
  const [tab, setTab] = useState<Tab>("chat");
  const [prevTab, setPrevTab] = useState<Tab>("chat");
  // sessionId for ImagePanel — stable across renders, client-only
  const [sessionId] = useState(() =>
    typeof crypto !== "undefined" ? crypto.randomUUID() : "session-1",
  );

  function switchTab(t: Tab) {
    setPrevTab(tab);
    setTab(t);
  }

  const dir = tab === "image" && prevTab === "chat" ? 1 : -1;

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-[#050d1a]">
      <ParticleBackground />

      <div
        className="fixed inset-0 z-[1] pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 80% 60% at 50% 110%, rgba(201,168,76,0.06) 0%, transparent 70%)",
        }}
      />

      <div className="relative z-10 flex flex-col h-full">
        {/* suppressHydrationWarning: Framer Motion writes initial-state inline styles server-side
            that differ from what React 19 computes on hydration */}
        <motion.header
          suppressHydrationWarning
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="relative z-30 flex-shrink-0 flex items-center justify-between px-5 py-3
                     bg-white/[0.03] backdrop-blur-xl border-b border-white/[0.06]"
        >
          <div className="flex items-center gap-3">
            <motion.div
              suppressHydrationWarning
              animate={{
                boxShadow: [
                  "0 0 8px rgba(201,168,76,0.2)",
                  "0 0 18px rgba(201,168,76,0.4)",
                  "0 0 8px rgba(201,168,76,0.2)",
                ],
              }}
              transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
              className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#0d1829] to-[#162240]
                         border border-[#c9a84c]/40 flex items-center justify-center"
            >
              <span className="text-[#c9a84c] text-lg">✝</span>
            </motion.div>
            <div>
              <h1 className="text-white font-bold tracking-wide text-sm leading-tight">
                FaithCompass
              </h1>
              <p className="text-[#c9a84c]/50 text-[10px] tracking-wider uppercase leading-tight">
                Scripture-grounded AI
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-white/25 text-xs hidden sm:block">
              Tradition
            </span>
            <DenominationSelector
              value={denomination}
              onChange={setDenomination}
            />
          </div>
        </motion.header>

        <motion.div
          suppressHydrationWarning
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.15 }}
          className="flex-shrink-0 flex border-b border-white/[0.06] bg-white/[0.02]"
        >
          {(["chat", "image"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => switchTab(t)}
              className="relative flex items-center gap-1.5 px-6 py-3 text-sm font-medium transition-colors"
            >
              <span
                className={
                  tab === t
                    ? "text-[#c9a84c]"
                    : "text-white/30 hover:text-white/60"
                }
              >
                {t === "chat" ? (
                  <MessageSquare size={14} />
                ) : (
                  <ImageIcon size={14} />
                )}
              </span>
              <span
                className={
                  tab === t
                    ? "text-[#c9a84c]"
                    : "text-white/30 hover:text-white/60"
                }
              >
                {t === "chat" ? "Chat" : "Image"}
              </span>
              {tab === t && (
                <motion.div
                  suppressHydrationWarning
                  layoutId="tab-indicator"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-[#c9a84c] to-transparent"
                />
              )}
            </button>
          ))}
        </motion.div>

        <div className="flex-1 overflow-hidden relative">
          <AnimatePresence mode="wait" custom={dir}>
            <motion.div
              suppressHydrationWarning
              key={tab}
              custom={dir}
              variants={TAB_VARIANTS}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
              className="absolute inset-0 overflow-hidden"
            >
              {tab === "chat" ? (
                <ChatInterface denomination={denomination} />
              ) : (
                <div className="h-full overflow-y-auto scrollbar-thin">
                  <ImagePanel
                    sessionId={sessionId}
                    denomination={denomination}
                  />
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
