import { useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import { useChatSessions } from "../../chat/ChatSessionContext";
import { useLang } from "../../i18n/LanguageContext";
import { LANGS } from "../../i18n/translations";
import type { ChatSession } from "../../types";
import {
  IconBook,
  IconChat,
  IconLogout,
  IconMaple,
  IconPin,
  IconPlus,
  IconQuiz,
  IconRoom,
  IconSearch,
  IconSidebar,
  IconTrash,
  IconUsers,
} from "../Icons";

function NavItem({
  to,
  label,
  icon,
  onClick,
}: {
  to: string;
  label: string;
  icon: React.ReactNode;
  onClick?: () => void;
}) {
  return (
    <NavLink
      to={to}
      end={to === "/"}
      onClick={onClick}
      className={({ isActive }) =>
        `flex items-center gap-3 rounded-[11px] px-3 py-2.5 text-sm font-medium transition ${
          isActive
            ? "bg-surface text-ink shadow-maple-sm"
            : "text-ink-soft hover:bg-surface hover:text-ink"
        }`
      }
    >
      <span className="text-accent">{icon}</span>
      {label}
    </NavLink>
  );
}

// Nhóm theo thời gian; trả về key ổn định để dịch lúc render (today/last7/older).
function groupByTime(sessions: ChatSession[]) {
  const now = Date.now();
  const day = 86400000;
  const groups: Record<string, ChatSession[]> = {};
  for (const s of sessions) {
    const t = s.created_at ? new Date(s.created_at).getTime() : now;
    const age = now - t;
    const key = age < day ? "today" : age < 7 * day ? "last7" : "older";
    (groups[key] = groups[key] || []).push(s);
  }
  return groups;
}

export function AppLayout() {
  const { user, logout } = useAuth();
  const { lang, setLang, t } = useLang();
  const navigate = useNavigate();
  const location = useLocation();
  const { sessions, setSessions, activeId, openSession, newChat } =
    useChatSessions();
  // Mặc định mở trên desktop, thu gọn trên mobile (drawer).
  const [open, setOpen] = useState(
    () => typeof window === "undefined" || window.innerWidth >= 1024
  );
  const [q, setQ] = useState("");

  const isAdmin = user?.role === "ADMIN";
  const isLecturer = user?.role === "LECTURER";
  const isStudent = user?.role === "USER";
  // Admin chỉ quản lý người dùng (không chat/quiz/phòng/tài liệu trong UI);
  // Giảng viên không dùng AI chat. Chỉ Sinh viên có mục Hỏi đáp + lịch sử.
  const hasChat = isStudent;
  const onChat = location.pathname === "/";

  // Trên mobile, đóng drawer sau khi điều hướng / chọn cuộc trò chuyện.
  const closeOnMobile = () => {
    if (window.innerWidth < 1024) setOpen(false);
  };

  const togglePin = async (e: React.MouseEvent, s: ChatSession) => {
    e.stopPropagation();
    const { data } = await api.patch<ChatSession>(`/sessions/${s.id}`, {
      pinned: !s.pinned,
    });
    setSessions(sessions.map((x) => (x.id === s.id ? data : x)));
  };

  const removeSession = async (e: React.MouseEvent, s: ChatSession) => {
    e.stopPropagation();
    if (!confirm(t("nav.deleteChatConfirm", { title: s.title }))) return;
    await api.delete(`/sessions/${s.id}`);
    setSessions(sessions.filter((x) => x.id !== s.id));
    if (s.id === activeId) newChat();
  };

  const filtered = sessions.filter((c) =>
    c.title.toLowerCase().includes(q.toLowerCase())
  );
  const pinned = filtered.filter((c) => c.pinned);
  const groups = groupByTime(filtered.filter((c) => !c.pinned));

  const renderRow = (c: ChatSession) => (
    <div
      key={c.id}
      onClick={() => {
        openSession(c.id);
        if (!onChat) navigate("/");
        closeOnMobile();
      }}
      className={`group relative flex cursor-pointer items-center rounded-[10px] text-[14.5px] transition ${
        c.id === activeId
          ? "bg-surface font-semibold text-ink"
          : "text-ink-soft hover:bg-surface hover:text-ink"
      }`}
    >
      <span className="min-w-0 flex-1 truncate px-2.5 py-2">{c.title}</span>
      <div
        className={`absolute right-1 flex items-center gap-0.5 rounded-[8px] pl-3 transition ${
          c.id === activeId
            ? "bg-surface"
            : "bg-surface opacity-0 group-hover:opacity-100"
        } ${c.pinned ? "opacity-100" : ""}`}
        style={{
          background: "linear-gradient(90deg, transparent, var(--surface) 28%)",
        }}
      >
        <button
          onClick={(e) => togglePin(e, c)}
          title={c.pinned ? t("nav.unpin") : t("nav.pin")}
          className={`grid h-7 w-7 place-items-center rounded-[7px] transition hover:bg-surface-2 ${
            c.pinned ? "text-accent" : "text-ink-faint hover:text-ink"
          }`}
        >
          <IconPin size={15} />
        </button>
        <button
          onClick={(e) => removeSession(e, c)}
          title={t("common.delete")}
          className="grid h-7 w-7 place-items-center rounded-[7px] text-ink-faint transition hover:bg-danger/10 hover:text-danger"
        >
          <IconTrash size={15} />
        </button>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen w-full overflow-hidden">
      {/* Backdrop cho drawer trên mobile */}
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/40 lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-[288px] flex-none flex-col border-r border-line bg-sidebar transition-transform duration-300 lg:static lg:z-auto lg:transition-[margin] ${
          open
            ? "translate-x-0 lg:ml-0"
            : "-translate-x-full lg:translate-x-0 lg:-ml-[289px]"
        }`}
        style={{ flex: "0 0 288px" }}
      >
        <div className="flex items-center justify-between px-4 pb-3 pt-[18px]">
          <div className="flex items-center gap-2.5">
            <span
              className="grid h-[34px] w-[34px] place-items-center rounded-[11px] text-white shadow-maple-sm"
              style={{ background: "var(--accent)" }}
            >
              <IconMaple size={22} />
            </span>
            <span className="text-xl font-bold tracking-tight">Maple</span>
          </div>
          <button
            className="grid h-[38px] w-[38px] place-items-center rounded-[11px] text-ink-soft transition hover:bg-surface-2 hover:text-ink"
            title={t("common.collapse")}
            onClick={() => setOpen(false)}
          >
            <IconSidebar size={20} />
          </button>
        </div>

        {hasChat && (
          <button
            className="mx-[14px] mb-3 mt-1 flex items-center gap-2.5 rounded-[13px] border border-line bg-surface px-3.5 py-3 text-[15px] font-semibold text-ink shadow-maple-sm transition hover:-translate-y-px hover:bg-surface-2"
            onClick={() => {
              newChat();
              if (!onChat) navigate("/");
              closeOnMobile();
            }}
          >
            <span className="text-accent">
              <IconPlus size={18} />
            </span>
            {t("nav.newChat")}
          </button>
        )}

        {/* App navigation */}
        <nav className="mx-[14px] mb-2 flex flex-col gap-1">
          {hasChat && (
            <NavItem to="/" label={t("nav.chat")} icon={<IconChat size={19} />} onClick={closeOnMobile} />
          )}
          {isLecturer && (
            <NavItem to="/documents" label={t("nav.documents")} icon={<IconBook size={19} />} onClick={closeOnMobile} />
          )}
          {!isAdmin && (
            <NavItem to="/rooms" label={t("nav.rooms")} icon={<IconRoom size={19} />} onClick={closeOnMobile} />
          )}
          {!isAdmin && (
            <NavItem to="/quizzes" label={t("nav.quiz")} icon={<IconQuiz size={19} />} onClick={closeOnMobile} />
          )}
          {isAdmin && (
            <NavItem to="/admin" label={t("nav.users")} icon={<IconUsers size={19} />} onClick={closeOnMobile} />
          )}
        </nav>

        {/* Conversation history (chỉ với role có chat) */}
        {hasChat ? (
          <>
            <div className="mx-[14px] mb-2 flex h-[42px] items-center gap-2 rounded-xl border border-line-soft bg-surface px-3 text-ink-faint">
              <IconSearch size={17} />
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder={t("nav.searchChat")}
                className="flex-1 border-none bg-transparent text-[14.5px] text-ink outline-none placeholder:text-ink-faint"
              />
            </div>

            <div className="flex-1 overflow-y-auto px-2 pb-2">
              {pinned.length > 0 && (
                <div className="mb-2">
                  <div className="flex items-center gap-1.5 px-2.5 pb-1.5 pt-2.5 text-xs font-semibold uppercase tracking-wider text-ink-faint">
                    <IconPin size={13} /> {t("nav.pinned")}
                  </div>
                  {pinned.map(renderRow)}
                </div>
              )}
              {Object.keys(groups).map((g) => (
                <div key={g} className="mb-2">
                  <div className="px-2.5 pb-1.5 pt-2.5 text-xs font-semibold uppercase tracking-wider text-ink-faint">
                    {t(`nav.${g}`)}
                  </div>
                  {groups[g].map(renderRow)}
                </div>
              ))}
              {filtered.length === 0 && (
                <div className="px-3 py-[18px] text-sm text-ink-faint">
                  {sessions.length === 0 ? t("nav.noChats") : t("nav.notFound")}
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1" />
        )}

        <div className="border-t border-line p-3">
          {/* Language switcher — VI / EN (web + mobile) */}
          <div
            className="mb-2 flex items-center gap-1 rounded-[11px] border border-line-soft bg-surface p-1"
            role="group"
            aria-label={t("nav.language")}
          >
            {LANGS.map((l) => (
              <button
                key={l.code}
                onClick={() => setLang(l.code)}
                className={`flex-1 rounded-[8px] py-1.5 text-xs font-semibold transition ${
                  lang === l.code
                    ? "bg-accent text-white shadow-maple-sm"
                    : "text-ink-soft hover:bg-surface-2 hover:text-ink"
                }`}
                title={l.label}
              >
                {l.short}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2.5 rounded-xl px-2 py-1.5">
            <div className="avatar avatar-user sm">
              {user?.full_name?.charAt(0) ?? "?"}
            </div>
            <div className="min-w-0 flex-1 leading-tight">
              <div className="truncate text-[14.5px] font-semibold">
                {user?.full_name}
              </div>
              <div className="flex items-center gap-1.5 text-[12.5px] text-ink-faint">
                <span className="truncate">{t(`role.${user?.role ?? "USER"}`)}</span>
              </div>
            </div>
            <button
              onClick={() => {
                logout();
                navigate("/login");
              }}
              className="grid h-9 w-9 place-items-center rounded-[10px] text-ink-faint transition hover:bg-surface-2 hover:text-danger"
              title={t("nav.logout")}
            >
              <IconLogout size={18} />
            </button>
          </div>
        </div>
      </aside>

      <main className="relative flex min-w-0 flex-1 flex-col bg-bg">
        {!open && (
          <button
            className="absolute left-3 top-[10px] z-10 hidden h-[38px] w-[38px] place-items-center rounded-[11px] text-ink-soft transition hover:bg-surface-2 hover:text-ink lg:grid"
            title={t("common.openSidebar")}
            onClick={() => setOpen(true)}
          >
            <IconSidebar size={20} />
          </button>
        )}
        <Outlet context={{ openSidebar: () => setOpen(true) }} />
      </main>
    </div>
  );
}
