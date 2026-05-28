import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import { MessageBubble } from "../components/chat/MessageBubble";
import type {
  ChatResponse,
  ChatSession,
  Course,
  Message,
  SessionDetail,
} from "../types";

export function ChatPage() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [courseId, setCourseId] = useState<number | null>(null);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const loadSessions = () =>
    api.get<ChatSession[]>("/sessions").then((r) => setSessions(r.data));

  useEffect(() => {
    loadSessions();
    api.get<Course[]>("/courses").then((r) => {
      setCourses(r.data);
      if (r.data[0]) setCourseId(r.data[0].id);
    });
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  const openSession = async (id: number) => {
    const { data } = await api.get<SessionDetail>(`/sessions/${id}`);
    setActiveId(id);
    setMessages(data.messages);
    if (data.course_id) setCourseId(data.course_id);
  };

  const newChat = () => {
    setActiveId(null);
    setMessages([]);
  };

  const send = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || sending) return;
    const question = input.trim();
    setInput("");
    setMessages((m) => [
      ...m,
      {
        id: Date.now(),
        role: "user",
        content: question,
        created_at: "",
        citations: [],
      },
    ]);
    setSending(true);
    try {
      const { data } = await api.post<ChatResponse>("/chat", {
        question,
        session_id: activeId,
        course_id: courseId,
      });
      setMessages((m) => [
        ...m,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: data.answer,
          created_at: "",
          citations: data.citations,
        },
      ]);
      if (!activeId) {
        setActiveId(data.session_id);
        loadSessions();
      }
    } catch {
      setMessages((m) => [
        ...m,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: "Xin lỗi, đã có lỗi khi xử lý câu hỏi của bạn.",
          created_at: "",
          citations: [],
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex h-full">
      {/* Sessions sidebar */}
      <div className="flex w-64 flex-col border-r border-slate-200 bg-white">
        <div className="p-4">
          <button
            onClick={newChat}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-brand-600 py-2.5 text-sm font-semibold text-white shadow-lg shadow-brand-600/20 transition hover:bg-brand-700"
          >
            ＋ Cuộc trò chuyện mới
          </button>
        </div>
        <p className="px-4 pb-1 text-xs font-semibold uppercase text-slate-400">
          Lịch sử
        </p>
        <div className="flex-1 space-y-1 overflow-y-auto px-2 pb-4">
          {sessions.length === 0 && (
            <p className="px-2 py-4 text-center text-xs text-slate-400">
              Chưa có cuộc trò chuyện nào.
            </p>
          )}
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => openSession(s.id)}
              className={`block w-full truncate rounded-lg px-3 py-2 text-left text-sm transition ${
                activeId === s.id
                  ? "bg-brand-50 font-medium text-brand-700"
                  : "text-slate-600 hover:bg-slate-50"
              }`}
            >
              {s.title}
            </button>
          ))}
        </div>
      </div>

      {/* Chat window */}
      <div className="flex flex-1 flex-col bg-slate-50">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
          <div>
            <h1 className="text-lg font-bold text-slate-800">Hỏi đáp tài liệu</h1>
            <p className="text-xs text-slate-400">
              Câu trả lời chỉ dựa trên tài liệu đã index
            </p>
          </div>
          <select
            value={courseId ?? ""}
            onChange={(e) => setCourseId(Number(e.target.value))}
            className="rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand-500"
          >
            {courses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </header>

        <div className="flex-1 space-y-6 overflow-y-auto px-6 py-6">
          {messages.length === 0 && <EmptyState />}
          {messages.map((m) => (
            <MessageBubble key={m.id} message={m} />
          ))}
          {sending && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>

        <form
          onSubmit={send}
          className="border-t border-slate-200 bg-white px-6 py-4"
        >
          <div className="flex items-end gap-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send(e);
                }
              }}
              rows={1}
              placeholder="Nhập câu hỏi về nội dung tài liệu…"
              className="max-h-32 flex-1 resize-none rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-200"
            />
            <button
              disabled={sending || !input.trim()}
              className="grid h-12 w-12 place-items-center rounded-2xl bg-brand-600 text-white shadow-lg shadow-brand-600/30 transition hover:bg-brand-700 disabled:opacity-40"
            >
              ➤
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function EmptyState() {
  const samples = [
    "Use case là gì?",
    "Phân biệt aggregation và composition",
    "Observer pattern hoạt động như thế nào?",
  ];
  return (
    <div className="flex h-full flex-col items-center justify-center text-center">
      <div className="grid h-16 w-16 place-items-center rounded-3xl bg-gradient-to-br from-brand-500 to-brand-700 text-3xl shadow-xl shadow-brand-600/30">
        🎓
      </div>
      <h2 className="mt-5 text-xl font-bold text-slate-700">
        Bắt đầu hỏi đáp
      </h2>
      <p className="mt-1 max-w-md text-sm text-slate-400">
        Đặt câu hỏi về nội dung tài liệu môn học. Trợ lý sẽ trả lời kèm trích
        dẫn nguồn.
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-2">
        {samples.map((s) => (
          <span
            key={s}
            className="rounded-full border border-slate-200 bg-white px-4 py-1.5 text-xs text-slate-500"
          >
            {s}
          </span>
        ))}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex animate-fade-in gap-3">
      <div className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 text-sm font-bold text-white">
        AI
      </div>
      <div className="flex items-center gap-1.5 rounded-2xl rounded-tl-sm border border-slate-100 bg-white px-4 py-4">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-2 w-2 animate-bounce rounded-full bg-brand-400"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  );
}
