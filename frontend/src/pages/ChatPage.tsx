import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import { MessageBubble } from "../components/chat/MessageBubble";
import {
  IconClose,
  IconFile,
  IconMaple,
  IconMic,
  IconMoon,
  IconPaperclip,
  IconSend,
  IconStop,
  IconSun,
} from "../components/Icons";
import { useTheme } from "../theme/ThemeContext";
import { useChatSessions } from "../chat/ChatSessionContext";
import type {
  Attachment,
  ChatResponse,
  ChatSession,
  Course,
  Message,
  SessionDetail,
} from "../types";

const SUGGESTED_PROMPTS = [
  { icon: "📐", title: "Use case là gì?", sub: "Giải thích khái niệm và vai trò trong mô hình hóa." },
  { icon: "🔗", title: "Aggregation vs Composition", sub: "Phân biệt hai loại quan hệ trong UML." },
  { icon: "🧩", title: "Observer Pattern", sub: "Mẫu thiết kế này hoạt động như thế nào?" },
  { icon: "🏛️", title: "Kiến trúc phân lớp", sub: "Mô tả layered software architecture." },
];

let _idc = 0;
const uid = () => Date.now() * 1000 + ++_idc;

export function ChatPage() {
  const { dark, toggle } = useTheme();
  const { sessions, setSessions, activeId, setActiveId, register } =
    useChatSessions();
  const [courses, setCourses] = useState<Course[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [courseId, setCourseId] = useState<number | null>(null);
  const [streaming, setStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const stopRef = useRef(false);

  const loadSessions = () =>
    api.get<ChatSession[]>("/sessions").then((r) => setSessions(r.data));

  useEffect(() => {
    loadSessions();
    api.get<Course[]>("/courses").then((r) => {
      setCourses(r.data);
      if (r.data[0]) setCourseId(r.data[0].id);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, streaming]);

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

  // let the sidebar (AppLayout) drive openSession / newChat
  useEffect(() => {
    register({ openSession, newChat });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Reveal the real backend answer word-by-word for a lively feel.
  const streamReply = useCallback((full: string, citations: Message["citations"]) => {
    const botId = uid();
    setMessages((m) => [
      ...m,
      { id: botId, role: "assistant", content: "", created_at: "", citations: [], streaming: true },
    ]);
    setStreaming(true);
    stopRef.current = false;
    const words = full.split(/(\s+)/);
    let idx = 0;
    const tick = () => {
      if (stopRef.current) {
        setMessages((m) =>
          m.map((x) =>
            x.id === botId ? { ...x, content: full, citations, streaming: false } : x
          )
        );
        setStreaming(false);
        return;
      }
      idx += Math.random() > 0.6 ? 2 : 1;
      const slice = words.slice(0, idx).join("");
      setMessages((m) => m.map((x) => (x.id === botId ? { ...x, content: slice } : x)));
      if (idx < words.length) {
        setTimeout(tick, 18 + Math.random() * 26);
      } else {
        setMessages((m) =>
          m.map((x) =>
            x.id === botId ? { ...x, content: full, citations, streaming: false } : x
          )
        );
        setStreaming(false);
      }
    };
    setTimeout(tick, 350);
  }, []);

  const send = useCallback(
    async (text: string, atts: Attachment[]) => {
      const question = text.trim();
      if (!question && atts.length === 0) return;
      const userMsg: Message = {
        id: uid(),
        role: "user",
        content: question || "(tệp đính kèm)",
        created_at: "",
        citations: [],
        attachments: atts.length ? atts : undefined,
      };
      setMessages((m) => [...m, userMsg]);
      // optimistic typing placeholder while we wait for the backend
      const placeholderId = uid();
      setMessages((m) => [
        ...m,
        { id: placeholderId, role: "assistant", content: "", created_at: "", citations: [], streaming: true },
      ]);
      setStreaming(true);
      try {
        const { data } = await api.post<ChatResponse>("/chat", {
          question,
          session_id: activeId,
          course_id: courseId,
        });
        // drop placeholder, then stream the real answer
        setMessages((m) => m.filter((x) => x.id !== placeholderId));
        setStreaming(false);
        streamReply(data.answer, data.citations);
        if (!activeId) {
          setActiveId(data.session_id);
          loadSessions();
        }
      } catch {
        setMessages((m) =>
          m.map((x) =>
            x.id === placeholderId
              ? {
                  ...x,
                  content: "Xin lỗi, đã có lỗi khi xử lý câu hỏi của bạn.",
                  streaming: false,
                }
              : x
          )
        );
        setStreaming(false);
      }
    },
    [activeId, courseId, streamReply]
  );

  const regenerate = useCallback(
    (botMsg: Message) => {
      const i = messages.findIndex((m) => m.id === botMsg.id);
      const prevUser = [...messages.slice(0, i)].reverse().find((m) => m.role === "user");
      setMessages((m) => m.filter((x) => x.id !== botMsg.id));
      if (prevUser) send(prevUser.content, []);
    },
    [messages, send]
  );

  const stop = () => {
    stopRef.current = true;
  };

  const activeTitle = activeId
    ? sessions.find((c) => c.id === activeId)?.title || "Maple"
    : "Maple";

  return (
    <div className="main flex h-full flex-col bg-bg">
      <header className="topbar sticky top-0 z-[5] flex h-[58px] flex-none items-center justify-between border-b border-line-soft px-4 backdrop-blur"
        style={{ background: "color-mix(in oklab, var(--bg) 85%, transparent)" }}>
        <div className="flex items-center gap-2">
          <span className="ml-1 text-base font-semibold tracking-tight">{activeTitle}</span>
        </div>
        <div className="flex items-center gap-2">
          {courses.length > 0 && (
            <select
              value={courseId ?? ""}
              onChange={(e) => setCourseId(Number(e.target.value))}
              className="rounded-xl border border-line bg-surface px-3 py-1.5 text-sm text-ink outline-none transition focus:border-accent/60"
            >
              {courses.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          )}
          <button
            className="grid h-[38px] w-[38px] place-items-center rounded-[11px] text-ink-soft transition hover:bg-surface-2 hover:text-ink"
            title="Đổi giao diện"
            onClick={toggle}
          >
            {dark ? <IconSun size={19} /> : <IconMoon size={19} />}
          </button>
        </div>
      </header>

      <div className="chat-scroll flex-1 overflow-y-auto scroll-smooth" ref={scrollRef}>
        {messages.length === 0 ? (
          <Welcome onPrompt={(p) => send(p, [])} />
        ) : (
          <div className="thread mx-auto flex max-w-[760px] flex-col gap-[26px] px-7 pb-6 pt-[30px]">
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} onRegenerate={regenerate} />
            ))}
          </div>
        )}
      </div>

      <Composer onSend={send} streaming={streaming} onStop={stop} />
    </div>
  );
}

function Welcome({ onPrompt }: { onPrompt: (p: string) => void }) {
  const hour = new Date().getHours();
  const greet = hour < 11 ? "Chào buổi sáng" : hour < 18 ? "Chào buổi chiều" : "Chào buổi tối";
  return (
    <div className="welcome">
      <div className="welcome-mark">
        <IconMaple size={52} />
      </div>
      <h1 className="welcome-title">{greet}! Mình là Maple 🍁</h1>
      <p className="welcome-sub">
        Mình trả lời dựa trên tài liệu môn học đã được index, kèm trích dẫn nguồn. Bắt đầu từ đâu nhỉ?
      </p>
      <div className="prompts">
        {SUGGESTED_PROMPTS.map((p, i) => (
          <button
            key={i}
            className="prompt-card"
            onClick={() => onPrompt(`${p.title} ${p.sub}`)}
          >
            <span className="prompt-emoji">{p.icon}</span>
            <span className="prompt-text">
              <strong>{p.title}</strong>
              <span>{p.sub}</span>
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

function Composer({
  onSend,
  streaming,
  onStop,
}: {
  onSend: (text: string, atts: Attachment[]) => void;
  streaming: boolean;
  onStop: () => void;
}) {
  const [text, setText] = useState("");
  const [atts, setAtts] = useState<Attachment[]>([]);
  const [rec, setRec] = useState(false);
  const taRef = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const grow = () => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 200) + "px";
  };
  useEffect(grow, [text]);

  const submit = () => {
    if (streaming) return;
    if (!text.trim() && atts.length === 0) return;
    onSend(text.trim(), atts);
    setText("");
    setAtts([]);
    requestAnimationFrame(() => {
      if (taRef.current) taRef.current.style.height = "auto";
    });
  };

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const onFiles = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = [...(e.target.files ?? [])].map((f) => ({
      name: f.name,
      size: f.size,
    }));
    setAtts((a) => [...a, ...files]);
    e.target.value = "";
  };

  return (
    <div className="composer-wrap">
      <div className="composer">
        {atts.length > 0 && (
          <div className="comp-atts">
            {atts.map((a, i) => (
              <div key={i} className="att-chip">
                <IconFile size={16} />
                <span>{a.name}</span>
                <button onClick={() => setAtts((x) => x.filter((_, j) => j !== i))}>
                  <IconClose size={13} />
                </button>
              </div>
            ))}
          </div>
        )}
        <div className="comp-row">
          <button
            className="comp-icon"
            title="Đính kèm"
            onClick={() => fileRef.current?.click()}
          >
            <IconPaperclip size={20} />
          </button>
          <input
            ref={fileRef}
            type="file"
            multiple
            hidden
            onChange={onFiles}
          />
          <textarea
            ref={taRef}
            rows={1}
            value={text}
            placeholder="Nhắn cho Maple…"
            onChange={(e) => setText(e.target.value)}
            onKeyDown={onKey}
          />
          <button
            className={`comp-icon ${rec ? "rec" : ""}`}
            title="Giọng nói"
            onClick={() => setRec((r) => !r)}
          >
            <IconMic size={20} />
          </button>
          {streaming ? (
            <button className="comp-send stop" onClick={onStop} title="Dừng">
              <IconStop size={18} />
            </button>
          ) : (
            <button
              className="comp-send"
              onClick={submit}
              disabled={!text.trim() && atts.length === 0}
              title="Gửi"
            >
              <IconSend size={18} />
            </button>
          )}
        </div>
      </div>
      <div className="comp-hint">
        Maple chỉ trả lời trong phạm vi tài liệu. Hãy kiểm tra các thông tin quan trọng.
      </div>
    </div>
  );
}
