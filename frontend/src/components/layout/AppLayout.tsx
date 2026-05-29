import { useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import { useChatSessions } from "../../chat/ChatSessionContext";
import {
  IconBook,
  IconChat,
  IconLogout,
  IconMaple,
  IconPlus,
  IconSearch,
  IconSidebar,
  IconUsers,
} from "../Icons";

const roleLabel: Record<string, string> = {
  ADMIN: "Quản trị viên",
  LECTURER: "Giảng viên",
  USER: "Sinh viên",
};

function NavItem({
  to,
  label,
  icon,
}: {
  to: string;
  label: string;
  icon: React.ReactNode;
}) {
  return (
    <NavLink
      to={to}
      end={to === "/"}
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

function groupByTime(sessions: { id: number; title: string; created_at: string }[]) {
  const now = Date.now();
  const day = 86400000;
  const groups: Record<string, typeof sessions> = {};
  for (const s of sessions) {
    const t = s.created_at ? new Date(s.created_at).getTime() : now;
    const age = now - t;
    const label =
      age < day ? "Hôm nay" : age < 7 * day ? "7 ngày qua" : "Trước đó";
    (groups[label] = groups[label] || []).push(s);
  }
  return groups;
}

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { sessions, activeId, openSession, newChat } = useChatSessions();
  const [open, setOpen] = useState(true);
  const [q, setQ] = useState("");

  const canManage = user?.role === "ADMIN" || user?.role === "LECTURER";
  const onChat = location.pathname === "/";

  const filtered = sessions.filter((c) =>
    c.title.toLowerCase().includes(q.toLowerCase())
  );
  const groups = groupByTime(filtered);

  return (
    <div className="flex h-screen w-full overflow-hidden">
      <aside
        className={`flex flex-col border-r border-line bg-sidebar transition-[margin] duration-300 ${
          open ? "" : "-ml-[289px]"
        }`}
        style={{ width: 288, flex: "0 0 288px" }}
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
            title="Thu gọn"
            onClick={() => setOpen(false)}
          >
            <IconSidebar size={20} />
          </button>
        </div>

        <button
          className="mx-[14px] mb-3 mt-1 flex items-center gap-2.5 rounded-[13px] border border-line bg-surface px-3.5 py-3 text-[15px] font-semibold text-ink shadow-maple-sm transition hover:-translate-y-px hover:bg-surface-2"
          onClick={() => {
            newChat();
            if (!onChat) navigate("/");
          }}
        >
          <span className="text-accent">
            <IconPlus size={18} />
          </span>
          Cuộc trò chuyện mới
        </button>

        {/* App navigation */}
        <nav className="mx-[14px] mb-2 flex flex-col gap-1">
          <NavItem to="/" label="Hỏi đáp" icon={<IconChat size={19} />} />
          {canManage && (
            <NavItem to="/documents" label="Tài liệu" icon={<IconBook size={19} />} />
          )}
          {user?.role === "ADMIN" && (
            <NavItem to="/admin" label="Người dùng" icon={<IconUsers size={19} />} />
          )}
        </nav>

        {/* Conversation history (only meaningful on chat) */}
        <div className="mx-[14px] mb-2 flex h-[42px] items-center gap-2 rounded-xl border border-line-soft bg-surface px-3 text-ink-faint">
          <IconSearch size={17} />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Tìm cuộc trò chuyện"
            className="flex-1 border-none bg-transparent text-[14.5px] text-ink outline-none placeholder:text-ink-faint"
          />
        </div>

        <div className="flex-1 overflow-y-auto px-2 pb-2">
          {Object.keys(groups).map((g) => (
            <div key={g} className="mb-2">
              <div className="px-2.5 pb-1.5 pt-2.5 text-xs font-semibold uppercase tracking-wider text-ink-faint">
                {g}
              </div>
              {groups[g].map((c) => (
                <button
                  key={c.id}
                  onClick={() => {
                    openSession(c.id);
                    if (!onChat) navigate("/");
                  }}
                  className={`block w-full truncate rounded-[10px] px-2.5 py-2 text-left text-[14.5px] transition ${
                    c.id === activeId
                      ? "bg-surface font-semibold text-ink"
                      : "text-ink-soft hover:bg-surface hover:text-ink"
                  }`}
                >
                  {c.title}
                </button>
              ))}
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="px-3 py-[18px] text-sm text-ink-faint">
              {sessions.length === 0
                ? "Chưa có cuộc trò chuyện nào."
                : "Không tìm thấy."}
            </div>
          )}
        </div>

        <div className="border-t border-line p-3">
          <div className="flex items-center gap-2.5 rounded-xl px-2 py-1.5">
            <div className="avatar avatar-user sm">
              {user?.full_name?.charAt(0) ?? "?"}
            </div>
            <div className="min-w-0 flex-1 leading-tight">
              <div className="truncate text-[14.5px] font-semibold">
                {user?.full_name}
              </div>
              <div className="text-[12.5px] text-ink-faint">
                {roleLabel[user?.role ?? "USER"]}
              </div>
            </div>
            <button
              onClick={() => {
                logout();
                navigate("/login");
              }}
              className="grid h-9 w-9 place-items-center rounded-[10px] text-ink-faint transition hover:bg-surface-2 hover:text-danger"
              title="Đăng xuất"
            >
              <IconLogout size={18} />
            </button>
          </div>
        </div>
      </aside>

      <main className="relative flex min-w-0 flex-1 flex-col bg-bg">
        {!open && (
          <button
            className="absolute left-3 top-[10px] z-10 grid h-[38px] w-[38px] place-items-center rounded-[11px] text-ink-soft transition hover:bg-surface-2 hover:text-ink"
            title="Mở thanh bên"
            onClick={() => setOpen(true)}
          >
            <IconSidebar size={20} />
          </button>
        )}
        <Outlet />
      </main>
    </div>
  );
}
