import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Role, User } from "../types";

const roleLabel: Record<Role, string> = {
  ADMIN: "Quản trị viên",
  LECTURER: "Giảng viên",
  USER: "Sinh viên",
};
const roleBadge: Record<Role, string> = {
  ADMIN: "bg-danger/15 text-danger",
  LECTURER: "bg-amber-500/15 text-amber-600 dark:text-amber-400",
  USER: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
};

export function AdminPage() {
  const [users, setUsers] = useState<User[]>([]);

  const load = () => api.get<User[]>("/users").then((r) => setUsers(r.data));
  useEffect(() => {
    load();
  }, []);

  const changeRole = async (id: number, role: Role) => {
    await api.patch(`/users/${id}/role`, { role });
    load();
  };

  return (
    <div className="h-full overflow-y-auto p-8">
      <div className="mx-auto max-w-4xl">
        <header className="mb-6">
          <h1 className="font-display text-2xl font-bold text-ink">
            Quản lý người dùng
          </h1>
          <p className="text-sm text-ink-faint">
            Xem danh sách và phân quyền cho người dùng trong hệ thống.
          </p>
        </header>

        <div className="overflow-hidden rounded-[20px] border border-line bg-surface">
          <div className="grid grid-cols-12 gap-3 border-b border-line bg-surface-2 px-5 py-3 text-xs font-semibold uppercase tracking-wide text-ink-faint">
            <div className="col-span-5">Người dùng</div>
            <div className="col-span-3">Vai trò hiện tại</div>
            <div className="col-span-4 text-right">Đổi vai trò</div>
          </div>
          {users.map((u) => (
            <div
              key={u.id}
              className="grid grid-cols-12 items-center gap-3 border-b border-line-soft px-5 py-3.5 transition last:border-0 hover:bg-surface-2/50"
            >
              <div className="col-span-5 flex items-center gap-3">
                <div className="avatar avatar-user sm">
                  {u.full_name.charAt(0)}
                </div>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-ink">
                    {u.full_name}
                  </p>
                  <p className="truncate text-xs text-ink-faint">{u.email}</p>
                </div>
              </div>
              <div className="col-span-3">
                <span
                  className={`rounded-full px-2.5 py-1 text-xs font-bold ${roleBadge[u.role]}`}
                >
                  {roleLabel[u.role]}
                </span>
              </div>
              <div className="col-span-4 text-right">
                <select
                  value={u.role}
                  onChange={(e) => changeRole(u.id, e.target.value as Role)}
                  className="rounded-xl border border-line bg-surface px-3 py-1.5 text-sm text-ink outline-none focus:border-accent"
                >
                  <option value="USER">Sinh viên</option>
                  <option value="LECTURER">Giảng viên</option>
                  <option value="ADMIN">Quản trị viên</option>
                </select>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
