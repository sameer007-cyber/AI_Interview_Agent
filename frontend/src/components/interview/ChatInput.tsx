"use client";

import { useState, useRef, KeyboardEvent } from "react";
import { motion } from "framer-motion";
import { Send, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (message: string) => void;
  loading: boolean;
  disabled: boolean;
  placeholder?: string;
}

export function ChatInput({ onSend, loading, disabled, placeholder }: ChatInputProps) {
  const [value, setValue] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  const submit = () => {
    if (!value.trim() || loading || disabled) return;
    onSend(value.trim());
    setValue("");
    if (ref.current) ref.current.style.height = "auto";
  };

  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="border-t border-stone-100 bg-[#faf8f5]/95 p-4 backdrop-blur-md"
    >
      <div className="max-w-3xl mx-auto">
        <div className={cn(
          "flex items-end gap-3 rounded-2xl bg-white p-3 border transition-all duration-200 shadow-sm",
          value.trim() ? "border-orange-300 shadow-orange-100" : "border-stone-200"
        )}>
          <textarea
            ref={ref}
            value={value}
            onChange={(e) => {
              setValue(e.target.value);
              e.target.style.height = "auto";
              e.target.style.height = `${Math.min(e.target.scrollHeight, 180)}px`;
            }}
            onKeyDown={(e: KeyboardEvent<HTMLTextAreaElement>) => {
              if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); }
            }}
            disabled={disabled || loading}
            placeholder={placeholder || "Type your answer..."}
            rows={1}
            className="flex-1 resize-none bg-transparent text-sm text-stone-800 placeholder:text-stone-300 focus:outline-none disabled:opacity-50"
            style={{ fontFamily: "'DM Sans', sans-serif" }}
          />
          <motion.button
            whileHover={value.trim() && !loading && !disabled ? { scale: 1.05 } : {}}
            whileTap={value.trim() && !loading && !disabled ? { scale: 0.95 } : {}}
            onClick={submit}
            disabled={!value.trim() || loading || disabled}
            className={cn(
              "flex h-8 w-8 shrink-0 items-center justify-center rounded-xl transition-all",
              value.trim() && !loading && !disabled
                ? "bg-orange-500 text-white shadow-sm shadow-orange-200"
                : "bg-stone-100 text-stone-300 cursor-not-allowed"
            )}
          >
            {loading
              ? <Loader2 className="h-4 w-4 animate-spin" />
              : <Send className="h-4 w-4" />
            }
          </motion.button>
        </div>
        <p className="mt-2 text-center text-[10px] text-stone-300">
          Powered by LangGraph + Groq — answers evaluated by AI
        </p>
      </div>
    </motion.div>
  );
}
