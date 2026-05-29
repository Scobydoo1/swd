export type Role = "ADMIN" | "LECTURER" | "USER";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  created_at: string;
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
