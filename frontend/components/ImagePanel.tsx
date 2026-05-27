"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Wand2, AlertTriangle, Download, ZoomIn } from "lucide-react";
import { generateImage } from "@/lib/api";
import type { Denomination } from "@/lib/types";

interface Props {
  sessionId: string;
  denomination: Denomination;
}

const EXAMPLE_PROMPTS = [
  "A dove descending through golden light over still water at dawn",
  "The Good Shepherd carrying a lamb through a green valley",
  "A glowing cross on a hilltop at sunset with radiant beams",
  "Byzantine icon of the Holy Trinity surrounded by golden light",
  "An open Bible with rays of light emanating from its pages",
];

export default function ImagePanel({ sessionId, denomination }: Props) {
  const [prompt, setPrompt] = useState("");
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [enhancedPrompt, setEnhancedPrompt] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [zoom, setZoom] = useState(false);

  async function handleGenerate() {
    if (!prompt.trim() || loading) return;
    setLoading(true);
    setImageUrl(null);
    setEnhancedPrompt(null);
    setError(null);
    try {
      const res = await generateImage({
        session_id: sessionId,
        prompt,
        denomination,
      });
      if (res.safety_flag) {
        setError(res.safety_flag.message);
      } else {
        setImageUrl(res.image_url);
        setEnhancedPrompt(res.enhanced_prompt);
      }
    } catch {
      setError("Could not reach the server. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-5 p-5 max-w-xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-white/90 font-bold text-lg flex items-center gap-2">
          <span className="text-xl">🎨</span> Christian Image Generation
        </h2>
        <p className="text-white/35 text-xs mt-0.5">
          Describe a scene, symbol, or story — powered by Pollinations.ai (free)
        </p>
      </div>

      {/* Example chips */}
      <div className="flex flex-wrap gap-2">
        {EXAMPLE_PROMPTS.map((p) => (
          <motion.button
            key={p}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => setPrompt(p)}
            className="text-xs px-3 py-1.5 rounded-full border border-[#c9a84c]/20 text-[#c9a84c]/60
                       hover:border-[#c9a84c]/50 hover:text-[#c9a84c] bg-[#c9a84c]/5 transition-colors truncate max-w-[240px]"
          >
            {p.length > 40 ? p.slice(0, 38) + "…" : p}
          </motion.button>
        ))}
      </div>

      {/* Prompt input */}
      <div className="flex flex-col gap-2">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe a Christian image in detail…"
          rows={3}
          className="w-full bg-white/[0.04] border border-white/[0.08] focus:border-[#c9a84c]/40
                     rounded-xl px-4 py-3 text-white/90 text-sm placeholder-white/20
                     focus:outline-none resize-none transition-colors backdrop-blur-sm"
        />
        <motion.button
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleGenerate}
          disabled={!prompt.trim() || loading}
          className="flex items-center justify-center gap-2 rounded-xl py-3 font-semibold text-sm
                     bg-gradient-to-r from-[#c9a84c] to-[#e8c86a] text-[#0a0f1e]
                     disabled:opacity-30 disabled:cursor-not-allowed
                     shadow-lg shadow-[#c9a84c]/20 transition-opacity"
        >
          <Wand2 size={15} />
          {loading ? "Generating…" : "Generate Image"}
        </motion.button>
      </div>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="flex items-start gap-2 rounded-xl bg-amber-950/60 border border-amber-500/25 px-3 py-2.5 text-amber-300 text-sm"
          >
            <AlertTriangle size={14} className="mt-0.5 flex-shrink-0" />
            <span>{error}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading skeleton */}
      <AnimatePresence>
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="rounded-2xl border border-white/[0.08] bg-white/[0.03] aspect-square flex flex-col items-center justify-center gap-4"
          >
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
              className="w-10 h-10 rounded-full border-2 border-[#c9a84c]/20 border-t-[#c9a84c]"
            />
            <div className="text-center">
              <p className="text-white/50 text-sm">Painting your vision…</p>
              <p className="text-white/25 text-xs mt-1">
                This may take up to 60 seconds
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Generated image */}
      <AnimatePresence>
        {imageUrl && (
          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="flex flex-col gap-3"
          >
            {/* Image container */}
            <div
              className="relative group rounded-2xl overflow-hidden border border-[#c9a84c]/20 cursor-zoom-in"
              onClick={() => setZoom(true)}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={imageUrl}
                alt="Generated Christian art"
                className="w-full object-cover"
                onError={() =>
                  setError(
                    "Image failed to load — generation service may be busy.",
                  )
                }
              />
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
                <ZoomIn
                  size={28}
                  className="text-white opacity-0 group-hover:opacity-80 transition-opacity"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              <a
                href={imageUrl}
                download="faithcompass-art.jpg"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-xs text-[#c9a84c]/60 hover:text-[#c9a84c] transition-colors"
              >
                <Download size={12} /> Save image
              </a>
            </div>

            {enhancedPrompt && (
              <details className="text-[10px] text-white/25 cursor-pointer">
                <summary className="hover:text-white/40 transition-colors">
                  View enhanced prompt
                </summary>
                <p className="mt-1.5 bg-white/[0.03] rounded-lg p-2.5 leading-relaxed text-white/30">
                  {enhancedPrompt}
                </p>
              </details>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Zoom lightbox */}
      <AnimatePresence>
        {zoom && imageUrl && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setZoom(false)}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm cursor-zoom-out p-6"
          >
            <motion.img
              initial={{ scale: 0.85 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.85 }}
              transition={{ ease: [0.16, 1, 0.3, 1] }}
              src={imageUrl}
              alt="Zoomed"
              className="max-w-full max-h-full rounded-2xl shadow-2xl"
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
