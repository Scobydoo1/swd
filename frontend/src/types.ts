export type Role = "ADMIN" | "LECTURER" | "USER";
export type Plan = "FREE" | "PRO" | "MAX";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  plan: Plan;
  created_at: string;
}

export interface PlanOption {
  id: Plan;
  name: string;
  price: number;
  price_label: string;
  tagline: string;
  features: string[];
  highlight: boolean;
  current: boolean;
}

export interface QuizListItem {
  id: number;
  course_id: number;
  title: string;
  num_questions: number;
  created_at: string;
}

export interface QuizQuestion {
  id: number;
  text: string;
  options: string[];
}

export interface QuizDetail {
  id: number;
  course_id: number;
  title: string;
  questions: QuizQuestion[];
}

export interface QuestionResult {
  question_id: number;
  your_index: number | null;
  correct_index: number;
  is_correct: boolean;
}

export interface AttemptResult {
  score: number;
  correct: number;
  total: number;
  results: QuestionResult[];
}

export interface QuizAttemptRow {
  id: number;
  user_id: number | null;
  user_name: string | null;
  user_email: string | null;
  score: number;
  created_at: string;
}

export interface Room {
  id: number;
  name: string;
  description: string;
  course_id: number;
  course_name: string;
  created_by: number | null;
  num_members: number;
  num_quizzes: number;
  created_at: string;
}

export interface RoomMember {
  user_id: number;
  full_name: string;
  email: string;
  added_at: string;
}

export interface RoomStudent {
  id: number;
  full_name: string;
  email: string;
}

export interface RoomDetail extends Room {
  members: RoomMember[];
  quizzes: QuizListItem[];
  documents: Document[];
}

export type RequestStatus = "PENDING" | "APPROVED" | "REJECTED";

export interface AccountRequest {
  id: number;
  email: string;
  full_name: string;
  requested_role: Role;
  message: string;
  status: RequestStatus;
  created_at: string;
  decided_at: string | null;
}

export interface ApproveResult {
  request: AccountRequest;
  email_sent: boolean;
  temp_password: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Course {
  id: number;
  name: string;
  description: string;
  owner_id: number | null;
}

export type DocStatus = "PROCESSING" | "INDEXED" | "FAILED";

export interface Document {
  id: number;
  course_id: number;
  chapter_id: number | null;
  filename: string;
  file_type: "PDF" | "DOCX" | "PPTX";
  status: DocStatus;
  num_chunks: number;
  created_at: string;
}

export interface Citation {
  source_text: string;
  document_name: string;
  page: number | null;
  score: number | null;
}

export interface ChatResponse {
  session_id: number;
  answer: string;
  citations: Citation[];
}

export interface ChatSession {
  id: number;
  title: string;
  course_id: number | null;
  pinned: boolean;
  created_at: string;
}

export interface Attachment {
  name: string;
  size?: number;
}

export interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  citations: Citation[];
  attachments?: Attachment[];
  streaming?: boolean;
}

export interface SessionDetail extends ChatSession {
  messages: Message[];
}
