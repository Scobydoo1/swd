import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { api } from "../api/client";
import { useLang } from "../i18n/LanguageContext";
import { IconSidebar } from "../components/Icons";
import type { Plan, Role, User } from "../types";

const roleBadge: Record<Role, string> = {
  ADMIN: "bg-danger/15 text-danger",
  LECTURER: "bg-amber-500/15 text-amber-600 dark:text-amber-400",
  USER: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
};

export function AdminPage() {
  const { t } = useLang();
  const { openSidebar } = useOutletContext<{ openSidebar: () => void }>();
  const [users, setUsers] = useState<User[]>([]);

  const load = () => api.get<User[]>("/users").then((r) => setUsers(r.data));
  useEffect(() => {
    load();
  }, []);

  const changeRole = async (id: number, role: Role) => {
    await api.patch(`/users/${id}/role`, { role });
    load();
  };

  const changePlan = async (id: number, plan: Plan) => {
    await api.patch(`/users/${id}/plan`, { plan });
    load();
  };

  return (
    <div className="h-full overflow-y-auto p-4 sm:p-8">
      <div className="mx-auto max-w-4xl">
        <header className="mb-6">
          <div className="flex items-center gap-2">
            <button
              onClick={() => openSidebar()}
              className="grid h-[36px] w-[36px] flex-none place-items-center rounded-[10px] text-ink-soft transition hover:bg-surface-2 hover:text-ink lg:hidden"
              title={t("common.openSidebar")}
            >
              <IconSidebar size={19} />
            </button>
            <h1 className="font-display text-2xl font-bold text-ink">
              {t("admin.title")}
            </h1>
          </div>
          <p className="mt-1 text-sm text-ink-faint">{t("admin.subtitle")}</p>
        </header>

        <div className="overflow-hidden rounded-[20px] border border-line bg-surface">
          <div className="grid grid-cols-12 gap-3 border-b border-line bg-surface-2 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-ink-faint sm:px-5">
            <div className="col-span-12 sm:col-span-4">{t("admin.colUser")}</div>
            <div className="hidden sm:col-span-4 sm:block">{t("admin.colRole")}</div>
            <div className="hidden sm:col-span-4 sm:block">{t("admin.colPlan")}</div>
          </div>
          {users.map((u) => (
            <div
              key={u.id}
              className="grid grid-cols-12 items-center gap-3 border-b border-line-soft px-4 py-3.5 transition last:border-0 hover:bg-surface-2/50 sm:px-5"
            >
              <div className="col-span-12 flex items-center gap-3 sm:col-span-4">
                <div className="avatar avatar-user sm">
                  {u.full_name.charAt(0)}
                </div>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-ink">
                    {u.full_name}
                  </p>
                  <p className="truncate text-xs text-ink-faint">{u.email}</p>
                </div>
                <span
                  className={`ml-auto flex-none rounded-full px-2 py-0.5 text-[10px] font-bold sm:hidden ${roleBadge[u.role]}`}
                >
                  {t(`role.${u.role}`)}
                </span>
              </div>
              <div className="col-span-6 sm:col-span-4">
                <select
                  value={u.role}
                  onChange={(e) => changeRole(u.id, e.target.value as Role)}
                  className="w-full rounded-xl border border-line bg-surface px-3 py-1.5 text-sm text-ink outline-none focus:border-accent"
                >
                  <option value="USER">{t("role.USER")}</option>
                  <option value="LECTURER">{t("role.LECTURER")}</option>
                  <option value="ADMIN">{t("role.ADMIN")}</option>
                </select>
              </div>
              <div className="col-span-6 sm:col-span-4">
                {u.role === "USER" ? (
                  <select
                    value={u.plan}
                    onChange={(e) => changePlan(u.id, e.target.value as Plan)}
                    className="w-full rounded-xl border border-line bg-surface px-3 py-1.5 text-sm text-ink outline-none focus:border-accent"
                  >
                    <option value="FREE">Free</option>
                    <option value="PRO">Pro</option>
                    <option value="MAX">Max</option>
                  </select>
                ) : (
                  <span className="block px-1 py-1.5 text-sm text-ink-faint">
                    {t("admin.notApplicable")}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
