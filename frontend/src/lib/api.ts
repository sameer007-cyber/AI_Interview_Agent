import axios, { AxiosInstance } from "axios";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 60000,
});

apiClient.interceptors.response.use(
  (r) => r,
  (error) => {
    console.error("[API Error]", error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
  message: string;
}

export interface SessionResponse {
  session_id: string;
  created_at: string;
  message: string;
}

export interface UploadResponse {
  session_id: string;
  document_type: string;
  filename: string;
  total_pages: number;
  total_chunks: number;
  message: string;
}

export interface SessionStatus {
  session_id: string;
  has_resume: boolean;
  has_job_description: boolean;
  resume_filename: string | null;
  jd_filename: string | null;
  ready_for_interview: boolean;
  message: string;
}

export interface InterviewStartResponse {
  session_id: string;
  message: string;
  first_message: string;
  interview_stage: string;
}

export interface InterviewMessageResponse {
  session_id: string;
  agent_message: string;
  interview_stage: string;
  current_question_number: number;
  total_questions: number;
  average_score: number | null;
  is_complete: boolean;
}

export const checkHealth = async (): Promise<HealthResponse> => {
  const r = await apiClient.get("/api/v1/health");
  return r.data;
};

export const createSession = async (): Promise<SessionResponse> => {
  const r = await apiClient.post("/api/v1/sessions");
  return r.data.data;
};

export const uploadDocument = async (
  sessionId: string,
  file: File,
  type: "resume" | "job-description"
): Promise<UploadResponse> => {
  const form = new FormData();
  form.append("file", file);
  const r = await apiClient.post(
    `/api/v1/sessions/${sessionId}/upload/${type}`,
    form,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return r.data.data;
};

export const getSessionStatus = async (sessionId: string): Promise<SessionStatus> => {
  const r = await apiClient.get(`/api/v1/sessions/${sessionId}/status`);
  return r.data.data;
};

export const startInterview = async (
  sessionId: string,
  candidateName: string,
  totalQuestions: number
): Promise<InterviewStartResponse> => {
  const r = await apiClient.post("/api/v1/interview/start", {
    session_id: sessionId,
    candidate_name: candidateName,
    total_questions: totalQuestions,
  });
  return r.data.data;
};

export const sendMessage = async (
  sessionId: string,
  message: string
): Promise<InterviewMessageResponse> => {
  const r = await apiClient.post("/api/v1/interview/message", {
    session_id: sessionId,
    message,
  });
  return r.data.data;
};
