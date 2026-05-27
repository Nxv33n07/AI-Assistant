"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Trash2 } from "lucide-react";
import { v4 as uuidv4 } from "uuid";
import MessageBubble from "./MessageBubble";
import { sendMessage, clearSession } from "@/lib/api";
import type { ChatMessage, Denomination } from "@/lib/types";

interface Props {
  denomination: Denomination;
}

const WELCOME: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content:
    "Peace be with you. I'm FaithCompass — your Scripture-grounded Christian AI companion.\n\nI can help you explore Bible passages, answer theological questions, write devotionals and prayers, and engage with the difficult questions of faith.\n\nAll Scripture I cite is verified in real-time. What's on your heart?",
  timestamp: new Date(),
};

function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 6 }}
      className="flex gap-3"
    >
      <div className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center bg-gradient-to-br from-[#0d1829] to-[#162240] border border-[#c9a84c]/40">
        <span className="text-[#c9a84c] text-xs">✝</span>
      </div>
      <div className="bg-white/[0.05] backdrop-blur-sm border border-white/[0.08] rounded-2xl rounded-tl-sm px-4 py-3.5 flex items-center gap-1.5">
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="w-1.5 h-1.5 rounded-full bg-[#c9a84c]/60"
            animate={{ y: [0, -5, 0], opacity: [0.4, 1, 0.4] }}
            transition={{
              duration: 1,
              repeat: Infinity,
              delay: i * 0.18,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>
    </motion.div>
  );
}

export default function ChatInterface({ denomination }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => uuidv4());
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 140)}px`;
  }, [input]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;
    setMessages((prev) => [
      ...prev,
      { id: uuidv4(), role: "user", content: text, timestamp: new Date() },
    ]);
    setInput("");
    setLoading(true);
    try {
      const res = await sendMessage({
        session_id: sessionId,
        message: text,
        denomination,
      });
      setMessages((prev) => [
        ...prev,
        {
          id: uuidv4(),
          role: "assistant",
          content: res.response,
          scripture_references: res.scripture_references,
          corrections: res.corrections,
          safety_flag: res.safety_flag,
          timestamp: new Date(),
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: uuidv4(),
          role: "assistant",
          content:
            "I couldn't reach the server. Please ensure the backend is running on port 8000.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
      textareaRef.current?.focus();
    }
  }

  async function handleClear() {
    await clearSession(sessionId).catch(() => {});
    setMessages([WELCOME]);
    setInput("");
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-5 flex flex-col gap-5 scrollbar-thin">
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          {loading && <TypingIndicator key="typing" />}
        </AnimatePresence>
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div
        className="flex-shrink-0 px-4 py-3 border-t border-white/[0.06]
                      bg-gradient-to-t from-[#050d1a]/80 to-transparent backdrop-blur-sm"
      >
        <div
          className="flex items-end gap-2 bg-white/[0.04] border border-white/[0.08] rounded-2xl px-3 py-2
                        focus-within:border-[#c9a84c]/40 transition-colors"
        >
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={handleClear}
            title="Clear conversation"
            className="flex-shrink-0 p-1.5 rounded-lg text-white/20 hover:text-white/50 hover:bg-white/[0.06] transition-colors mb-0.5"
          >
            <Trash2 size={14} />
          </motion.button>

          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask a theology question, cite a verse, request a devotional… (Enter to send)"
            rows={1}
            className="flex-1 bg-transparent text-white/90 text-sm placeholder-white/20
                       focus:outline-none resize-none leading-relaxed py-1"
          />

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.92 }}
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center mb-0.5
                       bg-gradient-to-br from-[#c9a84c] to-[#e8c86a]
                       disabled:opacity-25 disabled:cursor-not-allowed
                       shadow-lg shadow-[#c9a84c]/20 transition-opacity"
          >
            <Send size={14} className="text-[#0a0f1e]" />
          </motion.button>
        </div>
        <p className="text-center text-white/[0.12] text-[9px] mt-2 tracking-wide">
          Verses verified live · FaithCompass v1.0
        </p>
      </div>
    </div>
  );
}
