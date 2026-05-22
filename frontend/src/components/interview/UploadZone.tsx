"use client";

import { useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileText, CheckCircle2, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface UploadZoneProps {
  label: string;
  description: string;
  onUpload: (file: File) => Promise<void>;
  uploaded: boolean;
  filename?: string;
  disabled?: boolean;
}

export function UploadZone({ label, description, onUpload, uploaded, filename, disabled }: UploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);

  const handle = async (file: File) => {
    if (!file || !file.name.endsWith(".pdf")) return;
    setLoading(true);
    try { await onUpload(file); } finally { setLoading(false); }
  };

  return (
    <motion.div
      whileHover={!uploaded && !disabled ? { scale: 1.01 } : {}}
      whileTap={!uploaded && !disabled ? { scale: 0.99 } : {}}
      onClick={() => !disabled && !uploaded && inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => { e.preventDefault(); setDragging(false); const f = e.dataTransfer.files[0]; if (f) handle(f); }}
      className={cn(
        "relative cursor-pointer rounded-2xl border-2 border-dashed p-6 transition-all duration-200",
        uploaded
          ? "border-emerald-300 bg-emerald-50 cursor-default"
          : dragging
          ? "border-orange-400 bg-orange-50 scale-[1.01]"
          : "border-stone-200 bg-white hover:border-orange-300 hover:bg-orange-50/30",
        disabled && "cursor-not-allowed opacity-50"
      )}
    >
      <input ref={inputRef} type="file" accept=".pdf" className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handle(f); }} />

      <div className="flex items-center gap-4">
        <motion.div
          animate={uploaded ? { scale: [1, 1.2, 1] } : {}}
          transition={{ duration: 0.4 }}
          className={cn(
            "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl",
            uploaded ? "bg-emerald-100" : "bg-stone-100"
          )}
        >
          {loading
            ? <Loader2 className="h-5 w-5 animate-spin text-orange-500" />
            : uploaded
            ? <CheckCircle2 className="h-5 w-5 text-emerald-600" />
            : <Upload className="h-5 w-5 text-stone-400" />
          }
        </motion.div>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-stone-800">{label}</p>
          <AnimatePresence mode="wait">
            {uploaded && filename ? (
              <motion.p
                key="uploaded"
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-0.5 flex items-center gap-1.5 text-xs text-emerald-600"
              >
                <FileText className="h-3 w-3" />
                {filename}
              </motion.p>
            ) : (
              <motion.p key="desc" className="mt-0.5 text-xs text-stone-400">
                {description}
              </motion.p>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}
