import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";

const roleLabel: Record<string, string> = {
  ADMIN: "Quản trị viên",
  LECTURER: "Giảng viên",
  USER: "Sinh viên",
};

const roleBadge: Record<string, string> = {
  ADMIN: "bg-rose-100 text-rose-700",
  LECTURER: "bg-amber-100 text-amber-700",
  USER: "bg-emerald-100 text-emerald-700",
};

function NavItem({
  to,
  label,
  icon,
}: {
  to: string;
  label: string;
  icon: string;
}) {
  return (
    <NavLink
      to={to}
      end={to === "/"}
      className={({ isActive }) =>
        `flex items-center gap-3 rounded-xl px-4 py-2.5 text-sm font-medium transition ${
          isActive
            ? "bg-brand-600 text-white shadow-lg shadow-brand-600/30"
            : "text-slate-600 hover:bg-brand-50 hover:text-brand-700"
        }`
      }
    >
      <span className="text-lg">{icon}</span>
      {label}
    </NavLink>
  );
}

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const canManage = user?.role === "ADMIN" || user?.role === "LECTURER";

  return (
    <div className="flex h-screen bg-slate-50">
      <aside className="flex w-72 flex-col border-r border-slate-200 bg-white">
        <div className="flex items-center gap-3 px-6 py-6">
          <div className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 text-xl font-extrabold text-white shadow-lg shadow-brand-600/30">
            E
          </div>
          <div>
            <p className="text-lg font-extrabold tracking-tight text-slate-800">
              EduRAG
            </p>
            <p className="text-xs text-slate-400">Trợ lý học tập AI</p>
          </div>
        </div>

        <nav className="flex flex-1 flex-col gap-1.5 px-4">
          <NavItem to="/" label="Hỏi đáp" icon="💬" />
          {canManage && (
            <NavItem to="/documents" label="Tài liệu" icon="📚" />
          )}
          {user?.role === "ADMIN" && (
            <NavItem to="/admin" label="Người dùng" icon="👥" />
          )}
        </nav>

        <div className="m-4 rounded-2xl bg-slate-50 p-4">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-full bg-brand-100 font-bold text-brand-700">
              {user?.full_name?.charAt(0) ?? "?"}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-slate-700">
                {user?.full_name}
              </p>
              <span
                className={`mt-0.5 inline-block rounded-full px-2 py-0.5 text-[10px] font-bold ${
                  roleBadge[user?.role ?? "USER"]
                }`}
              >
                {roleLabel[user?.role ?? "USER"]}
              </span>
            </div>
          </div>
          <button
            onClick={() => {
              logout();
              navigate("/login");
            }}
            className="mt-3 w-full rounded-xl border border-slate-200 py-2 text-sm font-medium text-slate-500 transition hover:border-rose-200 hover:bg-rose-50 hover:text-rose-600"
          >
            Đăng xuất
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
