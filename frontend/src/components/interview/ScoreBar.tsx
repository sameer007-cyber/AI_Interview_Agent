"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

export function ScoreBar({ score, total, current }: { score: number; total: number; current: number }) {
  const pct = (score / 10) * 100;
  const color =
    score >= 8 ? "bg-emerald-500" :
    score >= 6 ? "bg-orange-500" :
    score >= 4 ? "bg-amber-400" :
    "bg-red-400";

  const textColor =
    score >= 8 ? "text-emerald-600" :
    score >= 6 ? "text-orange-600" :
    score >= 4 ? "text-amber-600" :
    "text-red-500";

  return (
    <div className="space-y-2 px-4 py-3 border-b border-stone-100 bg-white/60 backdrop-blur-sm">
      <div className="flex items-center justify-between text-xs max-w-3xl mx-auto">
        <span className="text-stone-400 font-medium">Question {current} of {total}</span>
        <span className={cn("font-mono font-bold text-sm", textColor)}>
          {score.toFixed(1)}/10
        </span>
      </div>
      <div className="h-1.5 w-full max-w-3xl mx-auto rounded-full bg-stone-100 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className={cn("h-full rounded-full", color)}
        />
      </div>
    </div>
  );
}
