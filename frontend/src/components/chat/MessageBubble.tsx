import ReactMarkdown from "react-markdown";
import type { Message } from "../../types";
import { CitationList } from "./CitationCard";

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <div
      className={`flex animate-fade-in gap-3 ${
        isUser ? "flex-row-reverse" : ""
      }`}
    >
      <div
        className={`grid h-9 w-9 shrink-0 place-items-center rounded-xl text-sm font-bold text-white ${
          isUser
            ? "bg-slate-700"
            : "bg-gradient-to-br from-brand-500 to-brand-700"
        }`}
      >
        {isUser ? "Bạn" : "AI"}
      </div>
      <div className={`max-w-[78%] ${isUser ? "items-end" : ""}`}>
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
            isUser
              ? "rounded-tr-sm bg-brand-600 text-white"
              : "rounded-tl-sm border border-slate-100 bg-white text-slate-700"
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose-chat">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>
        {!isUser && <CitationList citations={message.citations} />}
      </div>
    </div>
  );
}
