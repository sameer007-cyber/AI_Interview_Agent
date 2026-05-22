"use client";

import { motion } from "framer-motion";
import { BrainCircuit, User } from "lucide-react";
import { Message } from "@/types";
import { formatTime, cn } from "@/lib/utils";

function renderContent(content: string) {
  return content.split("\n").map((line, i) => {
    const parts = line.split(/\*\*(.*?)\*\*/g);
    return (
      <p key={i} className={cn("leading-relaxed", line === "" && "mt-2")}>
        {parts.map((part, j) =>
          j % 2 === 1
            ? <strong key={j} className="font-semibold text-stone-900">{part}</strong>
            : part
        )}
      </p>
    );
  });
}

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={cn("flex gap-3 px-4 py-3", isUser ? "flex-row-reverse" : "flex-row")}
    >
      <div className={cn(
        "flex h-8 w-8 shrink-0 items-center justify-center rounded-full border",
        isUser
          ? "bg-orange-500 border-orange-400"
          : "bg-white border-stone-200 shadow-sm"
      )}>
        {isUser
          ? <User className="h-4 w-4 text-white" />
          : <BrainCircuit className="h-4 w-4 text-stone-500" />
        }
      </div>

      <div className={cn("max-w-[80%] space-y-1", isUser ? "items-end" : "items-start")}>
        <div className={cn(
          "rounded-2xl px-4 py-3 text-sm shadow-sm",
          isUser
            ? "rounded-tr-sm bg-orange-500 text-white"
            : "rounded-tl-sm bg-white text-stone-700 border border-stone-100"
        )}>
          <div className="space-y-1">{renderContent(message.content)}</div>
        </div>
        <p className={cn("text-[10px] text-stone-400", isUser ? "text-right" : "text-left")}>
          {formatTime(message.timestamp)}
        </p>
      </div>
    </motion.div>
  );
}
