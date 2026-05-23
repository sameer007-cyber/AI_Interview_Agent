"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Header } from "@/components/layout/Header";
import { UploadZone } from "@/components/interview/UploadZone";
import { MessageBubble } from "@/components/interview/MessageBubble";
import { ChatInput } from "@/components/interview/ChatInput";
import { ScoreBar } from "@/components/interview/ScoreBar";
import { AppStage, Message, InterviewState } from "@/types";
import { checkHealth, createSession, uploadDocument, startInterview, sendMessage } from "@/lib/api";
import { BrainCircuit, Play, Trophy, ChevronRight, Loader2, User, Sparkles, FileText, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

const QUESTIONS_OPTIONS = [3, 5, 7, 10];

const fadeUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
};

const stagger = {
  animate: { transition: { staggerChildren: 0.08 } },
};

const defaultInterviewState: InterviewState = {
  sessionId: null,
  candidateName: "",
  totalQuestions: 5,
  currentQuestion: 0,
  averageScore: 0,
  isComplete: false,
  resumeFile: null,
  jdFile: null,
};

export default function HomePage() {
  const [mounted, setMounted] = useState(false);
  const [stage, setStage] = useState<AppStage>("landing");
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [interviewState, setInterviewState] = useState<InterviewState>(defaultInterviewState);

  // Prevent hydration mismatch — only render after mount
  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    checkHealth().then(() => setIsConnected(true)).catch(() => setIsConnected(false));
  }, [mounted]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const addMessage = (role: "user" | "assistant", content: string) => {
    setMessages((prev) => [...prev, {
      id: `${Date.now()}-${Math.random()}`,
      role,
      content,
      timestamp: new Date()
    }]);
  };

  const handleCreateSession = async () => {
    if (!interviewState.candidateName.trim()) { setError("Please enter your name"); return; }
    setLoading(true); setError(null);
    try {
      const session = await createSession();
      setInterviewState((s) => ({ ...s, sessionId: session.session_id }));
      setStage("uploading");
    } catch { setError("Failed to connect to backend. Make sure it is running on port 8000."); }
    finally { setLoading(false); }
  };

  const handleUpload = async (file: File, type: "resume" | "job-description") => {
    if (!interviewState.sessionId) return;
    try {
      const result = await uploadDocument(interviewState.sessionId, file, type);
      if (type === "resume") setInterviewState((s) => ({ ...s, resumeFile: result.filename }));
      else setInterviewState((s) => ({ ...s, jdFile: result.filename }));
    } catch { setError(`Failed to upload ${type}.`); }
  };

  const handleStartInterview = async () => {
    if (!interviewState.sessionId) return;
    setLoading(true); setError(null);
    try {
      const result = await startInterview(
        interviewState.sessionId,
        interviewState.candidateName,
        interviewState.totalQuestions
      );
      setStage("interviewing");
      addMessage("assistant", result.first_message);
    } catch (e: any) { setError(e.response?.data?.detail || "Failed to start interview"); }
    finally { setLoading(false); }
  };

  const handleSendMessage = useCallback(async (text: string) => {
    if (!interviewState.sessionId || loading) return;
    addMessage("user", text);
    setLoading(true);
    try {
      const result = await sendMessage(interviewState.sessionId, text);
      addMessage("assistant", result.agent_message);
      setInterviewState((s) => ({
        ...s,
        currentQuestion: result.current_question_number,
        averageScore: result.average_score || 0,
        isComplete: result.is_complete,
      }));
      if (result.is_complete) setStage("complete");
    } catch { addMessage("assistant", "Sorry, something went wrong. Please try again."); }
    finally { setLoading(false); }
  }, [interviewState.sessionId, loading]);

  const handleReset = () => {
    setStage("landing");
    setMessages([]);
    setError(null);
    setInterviewState(defaultInterviewState);
  };

  // Show nothing until client-side hydration is complete
  if (!mounted) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#faf8f5]">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-orange-500 flex items-center justify-center">
            <BrainCircuit className="h-5 w-5 text-white" />
          </div>
          <p className="text-sm text-stone-400">Loading...</p>
        </div>
      </div>
    );
  }

  // ─── LANDING ──────────────────────────────────────────────────────────────
  if (stage === "landing") return (
    <div className="flex min-h-screen flex-col bg-[#faf8f5]">
      <Header isConnected={isConnected} stage={stage} />

      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute top-0 right-0 h-[500px] w-[500px] rounded-full bg-orange-100/60 blur-[120px]" />
        <div className="absolute bottom-0 left-0 h-[400px] w-[400px] rounded-full bg-amber-100/40 blur-[100px]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[300px] w-[300px] rounded-full bg-stone-100/80 blur-[80px]" />
      </div>

      <main className="relative flex flex-1 flex-col items-center justify-center px-4 pt-14">
        <motion.div
          variants={stagger}
          initial="initial"
          animate="animate"
          className="w-full max-w-md space-y-8"
        >
          <motion.div variants={fadeUp} className="text-center space-y-5">
            <motion.div
              whileHover={{ rotate: [0, -5, 5, 0], scale: 1.05 }}
              transition={{ duration: 0.4 }}
              className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-orange-500 shadow-lg shadow-orange-200"
            >
              <BrainCircuit className="h-8 w-8 text-white" />
            </motion.div>
            <div>
              <h1 className="text-4xl font-bold tracking-tight text-stone-900"
                style={{ fontFamily: "'DM Serif Display', serif" }}>
                AI Interview<br />
                <span className="text-orange-500 italic">Agent</span>
              </h1>
              <p className="mt-3 text-sm text-stone-500 leading-relaxed">
                Upload your resume + job description.<br />
                Get grilled by an AI that knows your background.
              </p>
            </div>
          </motion.div>

          <motion.div
            variants={fadeUp}
            className="space-y-5 rounded-3xl border border-stone-100 bg-white p-7 shadow-xl shadow-stone-100"
          >
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-stone-400">
                Your Name
              </label>
              <div className="flex items-center gap-3 rounded-xl bg-stone-50 px-4 py-3 border border-stone-100 focus-within:border-orange-300 focus-within:bg-orange-50/30 transition-all">
                <User className="h-4 w-4 shrink-0 text-stone-300" />
                <input
                  type="text"
                  value={interviewState.candidateName}
                  onChange={(e) => setInterviewState((s) => ({ ...s, candidateName: e.target.value }))}
                  onKeyDown={(e) => e.key === "Enter" && handleCreateSession()}
                  placeholder="e.g. Sameer"
                  className="flex-1 bg-transparent text-sm text-stone-800 placeholder:text-stone-300 focus:outline-none"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-stone-400">
                Number of Questions
              </label>
              <div className="grid grid-cols-4 gap-2">
                {QUESTIONS_OPTIONS.map((n) => (
                  <motion.button
                    key={n}
                    whileHover={{ scale: 1.04 }}
                    whileTap={{ scale: 0.96 }}
                    onClick={() => setInterviewState((s) => ({ ...s, totalQuestions: n }))}
                    className={cn(
                      "rounded-xl py-2.5 text-sm font-semibold transition-all",
                      interviewState.totalQuestions === n
                        ? "bg-orange-500 text-white shadow-sm shadow-orange-200"
                        : "bg-stone-50 text-stone-500 hover:bg-stone-100 border border-stone-100"
                    )}
                  >
                    {n}
                  </motion.button>
                ))}
              </div>
            </div>

            <AnimatePresence>
              {error && (
                <motion.p
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="rounded-xl bg-red-50 px-3 py-2 text-xs text-red-500 border border-red-100"
                >
                  {error}
                </motion.p>
              )}
            </AnimatePresence>

            <motion.button
              whileHover={interviewState.candidateName.trim() ? { scale: 1.02 } : {}}
              whileTap={interviewState.candidateName.trim() ? { scale: 0.98 } : {}}
              onClick={handleCreateSession}
              disabled={loading || !interviewState.candidateName.trim()}
              className={cn(
                "flex w-full items-center justify-center gap-2 rounded-xl py-3.5 text-sm font-semibold transition-all",
                interviewState.candidateName.trim()
                  ? "bg-stone-900 text-white hover:bg-stone-800 shadow-sm"
                  : "cursor-not-allowed bg-stone-100 text-stone-300"
              )}
            >
              {loading
                ? <Loader2 className="h-4 w-4 animate-spin" />
                : <><span>Get Started</span><ChevronRight className="h-4 w-4" /></>
              }
            </motion.button>
          </motion.div>

          <motion.div variants={fadeUp} className="flex justify-center gap-3 flex-wrap">
            {[
              { icon: <FileText className="h-3 w-3" />, label: "Resume RAG" },
              { icon: <BrainCircuit className="h-3 w-3" />, label: "LangGraph" },
              { icon: <Zap className="h-3 w-3" />, label: "Groq LLM" },
              { icon: <Sparkles className="h-3 w-3" />, label: "AI Scoring" },
            ].map((f) => (
              <motion.div
                key={f.label}
                whileHover={{ scale: 1.05, y: -1 }}
                className="flex items-center gap-1.5 rounded-full border border-stone-200 bg-white px-3 py-1.5 text-xs font-medium text-stone-500 shadow-sm"
              >
                <span className="text-orange-400">{f.icon}</span>
                {f.label}
              </motion.div>
            ))}
          </motion.div>
        </motion.div>
      </main>
    </div>
  );

  // ─── UPLOADING ────────────────────────────────────────────────────────────
  if (stage === "uploading") {
    const bothUploaded = !!interviewState.resumeFile && !!interviewState.jdFile;
    return (
      <div className="flex min-h-screen flex-col bg-[#faf8f5]">
        <Header isConnected={isConnected} stage={stage} />
        <div className="pointer-events-none fixed inset-0 overflow-hidden">
          <div className="absolute top-0 right-0 h-[400px] w-[400px] rounded-full bg-orange-100/50 blur-[100px]" />
          <div className="absolute bottom-0 left-0 h-[300px] w-[300px] rounded-full bg-amber-100/40 blur-[80px]" />
        </div>
        <main className="relative flex flex-1 flex-col items-center justify-center px-4 pt-14">
          <motion.div
            variants={stagger}
            initial="initial"
            animate="animate"
            className="w-full max-w-md space-y-6"
          >
            <motion.div variants={fadeUp} className="text-center">
              <h2 className="text-2xl font-bold text-stone-900"
                style={{ fontFamily: "'DM Serif Display', serif" }}>
                Upload Documents
              </h2>
              <p className="mt-1 text-sm text-stone-500">
                Hey <span className="font-semibold text-orange-500">{interviewState.candidateName}</span>! Drop your files below.
              </p>
            </motion.div>

            <motion.div variants={fadeUp} className="space-y-3">
              <UploadZone
                label="Your Resume"
                description="PDF only — drag & drop or click to browse"
                onUpload={(f) => handleUpload(f, "resume")}
                uploaded={!!interviewState.resumeFile}
                filename={interviewState.resumeFile || undefined}
              />
              <UploadZone
                label="Job Description"
                description="PDF only — drag & drop or click to browse"
                onUpload={(f) => handleUpload(f, "job-description")}
                uploaded={!!interviewState.jdFile}
                filename={interviewState.jdFile || undefined}
              />
            </motion.div>

            <AnimatePresence>
              {error && (
                <motion.p
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="rounded-xl bg-red-50 px-3 py-2 text-xs text-red-500 border border-red-100"
                >
                  {error}
                </motion.p>
              )}
            </AnimatePresence>

            <AnimatePresence>
              {bothUploaded && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-center"
                >
                  <p className="text-xs font-medium text-emerald-700">
                    ✅ Both documents ready — let's start!
                  </p>
                </motion.div>
              )}
            </AnimatePresence>

            <motion.div variants={fadeUp}>
              <motion.button
                whileHover={bothUploaded ? { scale: 1.02 } : {}}
                whileTap={bothUploaded ? { scale: 0.98 } : {}}
                onClick={handleStartInterview}
                disabled={!bothUploaded || loading}
                className={cn(
                  "flex w-full items-center justify-center gap-2 rounded-xl py-3.5 text-sm font-semibold transition-all",
                  bothUploaded
                    ? "bg-stone-900 text-white hover:bg-stone-800 shadow-sm"
                    : "cursor-not-allowed bg-stone-100 text-stone-300"
                )}
              >
                {loading
                  ? <Loader2 className="h-4 w-4 animate-spin" />
                  : <><Play className="h-4 w-4" /><span>Start Interview ({interviewState.totalQuestions} questions)</span></>
                }
              </motion.button>
            </motion.div>
          </motion.div>
        </main>
      </div>
    );
  }

  // ─── INTERVIEWING + COMPLETE ──────────────────────────────────────────────
  return (
    <div className="flex h-screen flex-col bg-[#faf8f5]">
      <Header isConnected={isConnected} stage={stage} />

      {interviewState.currentQuestion > 0 && (
        <div className="mt-14">
          <ScoreBar
            score={interviewState.averageScore}
            total={interviewState.totalQuestions}
            current={interviewState.currentQuestion}
          />
        </div>
      )}

      <div className={cn("flex-1 overflow-y-auto", interviewState.currentQuestion === 0 && "mt-14")}>
        <div className="mx-auto max-w-3xl py-4">
          <AnimatePresence initial={false}>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
          </AnimatePresence>

          <AnimatePresence>
            {loading && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                className="flex items-center gap-3 px-4 py-3"
              >
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white border border-stone-100 shadow-sm">
                  <BrainCircuit className="h-4 w-4 text-stone-400" />
                </div>
                <div className="flex items-center gap-1 rounded-2xl rounded-tl-sm bg-white border border-stone-100 px-4 py-3 shadow-sm">
                  {[0, 1, 2].map((i) => (
                    <motion.span
                      key={i}
                      animate={{ scale: [1, 1.4, 1], opacity: [0.4, 1, 0.4] }}
                      transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.15 }}
                      className="h-1.5 w-1.5 rounded-full bg-stone-400 inline-block"
                    />
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {stage === "complete" && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="mx-4 my-6 rounded-3xl border border-amber-200 bg-gradient-to-br from-amber-50 to-orange-50 p-8 text-center shadow-lg shadow-amber-100"
              >
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
                >
                  <Trophy className="mx-auto h-12 w-12 text-amber-500" />
                </motion.div>
                <h3 className="mt-4 text-2xl font-bold text-stone-900"
                  style={{ fontFamily: "'DM Serif Display', serif" }}>
                  Interview Complete!
                </h3>
                <p className="mt-2 text-stone-600">
                  Final Score:{" "}
                  <span className="font-mono text-xl font-bold text-orange-500">
                    {interviewState.averageScore.toFixed(1)}
                    <span className="text-stone-400 text-base">/10</span>
                  </span>
                </p>
                <motion.button
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={handleReset}
                  className="mt-6 rounded-xl bg-stone-900 px-8 py-3 text-sm font-semibold text-white hover:bg-stone-800 transition-all shadow-sm"
                >
                  Start New Interview
                </motion.button>
              </motion.div>
            )}
          </AnimatePresence>

          <div ref={bottomRef} />
        </div>
      </div>

      {stage === "interviewing" && (
        <ChatInput
          onSend={handleSendMessage}
          loading={loading}
          disabled={interviewState.isComplete}
          placeholder={
            interviewState.currentQuestion === 0
              ? "Waiting for first question..."
              : "Type your answer... (Enter to send, Shift+Enter for new line)"
          }
        />
      )}
    </div>
  );
}
