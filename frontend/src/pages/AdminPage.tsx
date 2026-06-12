import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { useLang } from "../i18n/LanguageContext";
import { IconCheck, IconClose, IconSidebar, IconTrash } from "../components/Icons";
import type {
  AccountRequest,
  ApproveResult,
  Plan,
  Role,
  User,
} from "../types";

const roleBadge: Record<Role, string> = {
  ADMIN: "bg-danger/15 text-danger",
  LECTURER: "bg-amber-500/15 text-amber-600 dark:text-amber-400",
  USER: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
};

export function AdminPage() {
  const { t } = useLang();
  const { user: me } = useAuth();
  const { openSidebar } = useOutletContext<{ openSidebar: () => void }>();
  const [users, setUsers] = useState<User[]>([]);
  const [requests, setRequests] = useState<AccountRequest[]>([]);
  const [tab, setTab] = useState<"users" | "requests">("users");
  const [newEmail, setNewEmail] = useState("");
  const [newName, setNewName] = useState("");
  const [newRole, setNewRole] = useState<Role>("USER");
  const [creating, setCreating] = useState(false);
  const [deciding, setDeciding] = useState<number | null>(null);
  const [notice, setNotice] = useState<{ ok: boolean; text: string } | null>(
    null
  );

  const load = () => {
    api.get<User[]>("/users").then((r) => setUsers(r.data));
    api
      .get<AccountRequest[]>("/account-requests", {
        params: { status: "PENDING" },
      })
      .then((r) => setRequests(r.data));
  };
  useEffect(() => {
    load();
  }, []);

  // FR-REQ-03: Duyệt yêu cầu — backend tạo tài khoản + gửi email mật khẩu.
  const approveRequest = async (req: AccountRequest) => {
    setNotice(null);
    setDeciding(req.id);
    try {
      const { data } = await api.post<ApproveResult>(
        `/account-requests/${req.id}/approve`
      );
      setNotice({
        ok: true,
        text: data.email_sent
          ? t("admin.approved", { email: req.email })
          : t("admin.approvedNoEmail", { password: data.temp_password ?? "" }),
      });
      load();
    } catch (err: any) {
      setNotice({
        ok: false,
        text: err.response?.data?.detail ?? t("common.error"),
      });
    } finally {
      setDeciding(null);
    }
  };

  const rejectRequest = async (req: AccountRequest) => {
    if (!confirm(t("admin.rejectConfirm", { name: req.full_name, email: req.email })))
      return;
    setNotice(null);
    setDeciding(req.id);
    try {
      await api.post(`/account-requests/${req.id}/reject`);
      setNotice({ ok: true, text: t("admin.rejected", { email: req.email }) });
      load();
    } catch (err: any) {
      setNotice({
        ok: false,
        text: err.response?.data?.detail ?? t("common.error"),
      });
    } finally {
      setDeciding(null);
    }
  };

  // FR-ADM-01: Admin cấp tài khoản — mật khẩu tự sinh gửi qua email.
  const createUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setNotice(null);
    setCreating(true);
    try {
      const { data } = await api.post<{
        user: User;
        email_sent: boolean;
        temp_password: string | null;
      }>("/users", { email: newEmail, full_name: newName, role: newRole });
      setNotice({
        ok: true,
        text: data.email_sent
          ? t("admin.created", { email: data.user.email })
          : t("admin.createdNoEmail", { password: data.temp_password ?? "" }),
      });
      setNewEmail("");
      setNewName("");
      setNewRole("USER");
      load();
    } catch (err: any) {
      setNotice({
        ok: false,
        text: err.response?.data?.detail ?? t("common.error"),
      });
    } finally {
      setCreating(false);
    }
  };

  const changeRole = async (id: number, role: Role) => {
    await api.patch(`/users/${id}/role`, { role });
    load();
  };

  const changePlan = async (id: number, plan: Plan) => {
    await api.patch(`/users/${id}/plan`, { plan });
    load();
  };

  const removeUser = async (u: User) => {
    if (!confirm(t("admin.deleteUserConfirm", { name: u.full_name }))) return;
    try {
      await api.delete(`/users/${u.id}`);
      load();
    } catch (e: any) {
      alert(e.response?.data?.detail ?? t("admin.deleteUserFailed"));
    }
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

        {/* Tabs: Người dùng | Yêu cầu chờ duyệt */}
        <div className="mb-5 flex items-center gap-1 rounded-[14px] border border-line bg-surface p-1">
          {(
            [
              ["users", t("admin.tabUsers")],
              ["requests", `${t("admin.tabRequests")} (${requests.length})`],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex-1 rounded-[10px] py-2 text-sm font-semibold transition ${
                tab === key
                  ? "bg-accent text-white shadow-maple-sm"
                  : "text-ink-soft hover:bg-surface-2 hover:text-ink"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {notice && (
          <p
            className={`mb-4 rounded-xl px-4 py-2.5 text-sm ${
              notice.ok
                ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                : "bg-danger/10 text-danger"
            }`}
          >
            {notice.text}
          </p>
        )}

        {tab === "requests" ? (
          <div className="overflow-hidden rounded-[20px] border border-line bg-surface">
            {requests.length === 0 ? (
              <p className="p-8 text-center text-sm text-ink-faint">
                {t("admin.reqEmpty")}
              </p>
            ) : (
              requests.map((r) => (
                <div
                  key={r.id}
                  className="flex flex-col gap-3 border-b border-line-soft px-4 py-4 last:border-0 sm:flex-row sm:items-center sm:px-5"
                >
                  <div className="flex min-w-0 flex-1 items-center gap-3">
                    <div className="avatar avatar-user sm">
                      {r.full_name.charAt(0)}
                    </div>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-ink">
                        {r.full_name}
                        <span
                          className={`ml-2 rounded-full px-2 py-0.5 text-[10px] font-bold ${roleBadge[r.requested_role]}`}
                        >
                          {t(`role.${r.requested_role}`)}
                        </span>
                      </p>
                      <p className="truncate text-xs text-ink-faint">{r.email}</p>
                      {r.message && (
                        <p className="mt-1 text-xs text-ink-soft">
                          <span className="font-semibold">{t("admin.reqMessage")}</span>{" "}
                          {r.message}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex flex-none gap-2">
                    <button
                      onClick={() => approveRequest(r)}
                      disabled={deciding === r.id}
                      className="flex items-center gap-1.5 rounded-xl bg-accent px-3.5 py-2 text-sm font-semibold text-white transition hover:brightness-105 disabled:opacity-50"
                    >
                      <IconCheck size={15} />
                      {deciding === r.id ? t("admin.approving") : t("admin.approve")}
                    </button>
                    <button
                      onClick={() => rejectRequest(r)}
                      disabled={deciding === r.id}
                      className="flex items-center gap-1.5 rounded-xl border border-line px-3.5 py-2 text-sm font-semibold text-ink-soft transition hover:bg-danger/10 hover:text-danger disabled:opacity-50"
                    >
                      <IconClose size={15} /> {t("admin.reject")}
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        ) : (
          <>
        <form
          onSubmit={createUser}
          className="mb-6 rounded-[20px] border border-line bg-surface p-5"
        >
          <h2 className="font-display text-lg font-bold text-ink">
            {t("admin.createUser")}
          </h2>
          <p className="mt-1 text-xs text-ink-faint">
            {t("admin.createUserHint")}
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_1fr_auto_auto]">
            <input
              type="email"
              required
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              placeholder={t("admin.email")}
              className="rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink outline-none focus:border-accent placeholder:text-ink-faint"
            />
            <input
              required
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder={t("admin.fullName")}
              className="rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink outline-none focus:border-accent placeholder:text-ink-faint"
            />
            <select
              value={newRole}
              onChange={(e) => setNewRole(e.target.value as Role)}
              className="rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink outline-none focus:border-accent"
            >
              <option value="USER">{t("role.USER")}</option>
              <option value="LECTURER">{t("role.LECTURER")}</option>
            </select>
            <button
              disabled={creating}
              className="rounded-xl px-5 py-2 text-sm font-semibold text-white transition hover:brightness-105 disabled:opacity-60"
              style={{ background: "var(--accent)" }}
            >
              {creating ? t("admin.creating") : t("admin.create")}
            </button>
          </div>
        </form>

        <div className="overflow-hidden rounded-[20px] border border-line bg-surface">
          <div className="grid grid-cols-12 gap-3 border-b border-line bg-surface-2 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-ink-faint sm:px-5">
            <div className="col-span-12 sm:col-span-4">{t("admin.colUser")}</div>
            <div className="hidden sm:col-span-3 sm:block">{t("admin.colRole")}</div>
            <div className="hidden sm:col-span-3 sm:block">{t("admin.colPlan")}</div>
            <div className="hidden text-right sm:col-span-2 sm:block">{t("admin.colActions")}</div>
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
              <div className="col-span-6 sm:col-span-3">
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
              <div className="col-span-5 sm:col-span-3">
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
              <div className="col-span-1 flex justify-end sm:col-span-2">
                {u.id !== me?.id && (
                  <button
                    onClick={() => removeUser(u)}
                    title={t("admin.deleteUser")}
                    className="grid h-8 w-8 place-items-center rounded-lg text-ink-faint transition hover:bg-danger/10 hover:text-danger"
                  >
                    <IconTrash size={16} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
          </>
        )}
      </div>
    </div>
  );
}
