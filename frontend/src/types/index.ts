export type AppStage =
  | "landing"
  | "uploading"
  | "ready"
  | "interviewing"
  | "complete";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  score?: number;
}

export interface InterviewState {
  sessionId: string | null;
  candidateName: string;
  totalQuestions: number;
  currentQuestion: number;
  averageScore: number;
  isComplete: boolean;
  resumeFile: string | null;
  jdFile: string | null;
}
