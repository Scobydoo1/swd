import { useState } from "react";
import type { Message } from "../../types";
import { Markdown } from "../Markdown";
import { CitationList } from "./CitationCard";
import {
  IconCheck,
  IconCopy,
  IconFile,
  IconMaple,
  IconRefresh,
  IconThumbDown,
  IconThumbUp,
} from "../Icons";

interface Props {
  message: Message & { streaming?: boolean };
  bubbleUser?: boolean;
  onRegenerate?: (m: Message) => void;
}

function Avatar({ role }: { role: string }) {
  if (role === "assistant") {
    return (
      <div
        className="avatar avatar-bot"
        style={{ background: "var(--accent)" }}
      >
        <IconMaple size={20} />
      </div>
    );
  }
  return <div className="avatar avatar-user">B</div>;
}

function TypingDots() {
  return (
    <div className="typing">
      <span></span>
      <span></span>
      <span></span>
    </div>
  );
}

function CopyBtn({ text }: { text: string }) {
  const [c, setC] = useState(false);
  return (
    <button
      className="act-btn"
      title="Sao chép"
      onClick={() => {
        navigator.clipboard?.writeText(text).catch(() => {});
        setC(true);
        setTimeout(() => setC(false), 1500);
      }}
    >
      {c ? <IconCheck size={16} /> : <IconCopy size={16} />}
    </button>
  );
}

export function MessageBubble({ message, bubbleUser = true, onRegenerate }: Props) {
  const isUser = message.role === "user";
  const streaming = (message as { streaming?: boolean }).streaming;
  return (
    <div className={`msg animate-fade-in ${isUser ? "msg-user" : "msg-bot"}`}>
      <Avatar role={message.role} />
      <div className="msg-body">
        <div className="msg-name">{isUser ? "Bạn" : "Maple"}</div>

        {message.attachments && message.attachments.length > 0 && (
          <div className="msg-attachments mb-2 flex flex-wrap gap-2">
            {message.attachments.map((a, i) => (
              <div key={i} className="att-chip">
                <IconFile size={16} />
                <span>{a.name}</span>
              </div>
            ))}
          </div>
        )}

        <div className={`msg-content ${isUser && bubbleUser ? "bubble" : ""}`}>
          {message.role === "assistant" && streaming && message.content === "" ? (
            <TypingDots />
          ) : isUser ? (
            <p className="md-p whitespace-pre-wrap">{message.content}</p>
          ) : (
            <Markdown src={message.content} />
          )}
          {message.role === "assistant" && streaming && message.content !== "" && (
            <span className="caret" />
          )}
        </div>

        {!isUser && message.citations.length > 0 && (
          <CitationList citations={message.citations} />
        )}

        {message.role === "assistant" && !streaming && message.content && (
          <div className="msg-actions">
            <CopyBtn text={message.content} />
            {onRegenerate && (
              <button
                className="act-btn"
                title="Tạo lại"
                onClick={() => onRegenerate(message)}
              >
                <IconRefresh size={16} />
              </button>
            )}
            <button className="act-btn" title="Hữu ích">
              <IconThumbUp size={16} />
            </button>
            <button className="act-btn" title="Chưa tốt">
              <IconThumbDown size={16} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
