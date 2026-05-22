"use client";

import { motion } from "framer-motion";
import { BrainCircuit, Wifi, WifiOff } from "lucide-react";
import { cn } from "@/lib/utils";

interface HeaderProps {
  isConnected: boolean;
  stage: string;
}

export function Header({ isConnected, stage }: HeaderProps) {
  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="fixed top-0 left-0 right-0 z-50 h-14 border-b border-stone-200 bg-[#faf8f5]/90 backdrop-blur-md"
    >
      <div className="flex h-full items-center justify-between px-6 max-w-5xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-orange-500 shadow-sm shadow-orange-200">
            <BrainCircuit className="h-4 w-4 text-white" />
          </div>
          <span className="text-sm font-semibold tracking-tight text-stone-800" style={{ fontFamily: "'DM Serif Display', serif" }}>
            interview<span className="text-orange-500">.ai</span>
          </span>
        </div>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className={cn(
            "flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium border",
            isConnected
              ? "bg-emerald-50 text-emerald-700 border-emerald-200"
              : "bg-red-50 text-red-600 border-red-200"
          )}
        >
          {isConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
          {isConnected ? "connected" : "offline"}
        </motion.div>
      </div>
    </motion.header>
  );
}
