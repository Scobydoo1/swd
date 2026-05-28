import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Role, User } from "../types";

const roleLabel: Record<Role, string> = {
  ADMIN: "Quản trị viên",
  LECTURER: "Giảng viên",
  USER: "Sinh viên",
};
const roleBadge: Record<Role, string> = {
  ADMIN: "bg-rose-100 text-rose-700",
  LECTURER: "bg-amber-100 text-amber-700",
  USER: "bg-emerald-100 text-emerald-700",
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
          <h1 className="text-2xl font-extrabold text-slate-800">
            Quản lý người dùng
          </h1>
          <p className="text-sm text-slate-400">
            Xem danh sách và phân quyền cho người dùng trong hệ thống.
          </p>
        </header>

        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
          <div className="grid grid-cols-12 gap-3 border-b border-slate-100 bg-slate-50 px-5 py-3 text-xs font-semibold uppercase text-slate-400">
            <div className="col-span-5">Người dùng</div>
            <div className="col-span-3">Vai trò hiện tại</div>
            <div className="col-span-4 text-right">Đổi vai trò</div>
          </div>
          {users.map((u) => (
            <div
              key={u.id}
              className="grid grid-cols-12 items-center gap-3 border-b border-slate-50 px-5 py-3.5 transition hover:bg-slate-50/50"
            >
              <div className="col-span-5 flex items-center gap-3">
                <div className="grid h-9 w-9 place-items-center rounded-full bg-brand-100 text-sm font-bold text-brand-700">
                  {u.full_name.charAt(0)}
                </div>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-slate-700">
                    {u.full_name}
                  </p>
                  <p className="truncate text-xs text-slate-400">{u.email}</p>
                </div>
              </div>
              <div className="col-span-3">
                <span
                  className={`rounded-full px-2.5 py-1 text-xs font-bold ${
                    roleBadge[u.role]
                  }`}
                >
                  {roleLabel[u.role]}
                </span>
              </div>
              <div className="col-span-4 text-right">
                <select
                  value={u.role}
                  onChange={(e) => changeRole(u.id, e.target.value as Role)}
                  className="rounded-xl border border-slate-200 px-3 py-1.5 text-sm outline-none focus:border-brand-500"
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
