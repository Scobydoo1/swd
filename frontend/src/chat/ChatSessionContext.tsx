import { createContext, useContext, useMemo, useState } from "react";
import type { ChatSession } from "../types";

interface ChatSessionCtx {
  sessions: ChatSession[];
  setSessions: (s: ChatSession[]) => void;
  activeId: number | null;
  setActiveId: (id: number | null) => void;
  // set by ChatPage so the sidebar can trigger navigation actions
  openSession: (id: number) => void;
  newChat: () => void;
  register: (h: { openSession: (id: number) => void; newChat: () => void }) => void;
}

const Ctx = createContext<ChatSessionCtx>(null!);

export function ChatSessionProvider({ children }: { children: React.ReactNode }) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [handlers, setHandlers] = useState<{
    openSession: (id: number) => void;
    newChat: () => void;
  }>({ openSession: () => {}, newChat: () => {} });

  const value = useMemo(
    () => ({
      sessions,
      setSessions,
      activeId,
      setActiveId,
      openSession: handlers.openSession,
      newChat: handlers.newChat,
      register: setHandlers,
    }),
    [sessions, activeId, handlers]
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export const useChatSessions = () => useContext(Ctx);
