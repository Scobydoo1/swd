import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { useTheme } from "../theme/ThemeContext";
import { useLang } from "../i18n/LanguageContext";
import { GoogleSignInButton } from "../components/GoogleSignInButton";
import { IconClose, IconMaple, IconMoon, IconSun } from "../components/Icons";
import type { Role } from "../types";

export function LoginPage() {
  const { user, login, loginWithGoogle } = useAuth();
  const { dark, toggle } = useTheme();
  const { t } = useLang();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [requesting, setRequesting] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err: any) {
      setError(err.response?.data?.detail ?? t("common.error"));
    } finally {
      setBusy(false);
    }
  };

  const googleLogin = async (idToken: string) => {
    setError("");
    setBusy(true);
    try {
      await loginWithGoogle(idToken);
      navigate("/");
    } catch (err: any) {
      setError(err.response?.data?.detail ?? t("common.error"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg p-4">
      <button
        onClick={toggle}
        className="absolute right-5 top-5 grid h-[38px] w-[38px] place-items-center rounded-[11px] text-ink-soft transition hover:bg-surface-2 hover:text-ink"
        title={t("common.toggleTheme")}
      >
        {dark ? <IconSun size={19} /> : <IconMoon size={19} />}
      </button>

      <div className="grid w-full max-w-4xl overflow-hidden rounded-[28px] border border-line bg-surface shadow-maple md:grid-cols-2">
        {/* Brand panel */}
        <div
          className="hidden flex-col justify-between p-10 text-white md:flex"
          style={{
            background:
              "linear-gradient(150deg, var(--accent), color-mix(in oklab, var(--accent) 60%, #6b3318))",
          }}
        >
          <div>
            <div className="grid h-14 w-14 place-items-center rounded-2xl bg-white/20 backdrop-blur">
              <IconMaple size={30} />
            </div>
            <h1 className="mt-8 font-display text-3xl font-bold leading-tight">
              Maple 🍁
            </h1>
            <p className="mt-3 text-white/80">{t("login.tagline")}</p>
          </div>
          <ul className="space-y-3 text-sm text-white/85">
            <li className="flex items-center gap-2">{t("login.feature1")}</li>
            <li className="flex items-center gap-2">{t("login.feature2")}</li>
            <li className="flex items-center gap-2">{t("login.feature3")}</li>
          </ul>
        </div>

        {/* Form panel */}
        <div className="p-8 sm:p-10">
          <h2 className="font-display text-2xl font-bold text-ink">
            {t("login.signIn")}
          </h2>
          <p className="mt-1 text-sm text-ink-faint">{t("login.welcomeBack")}</p>

          <form onSubmit={submit} className="mt-6 space-y-4">
            <Field
              label={t("login.email")}
              type="email"
              value={email}
              onChange={setEmail}
              placeholder="you@example.com"
            />
            <Field
              label={t("login.password")}
              type="password"
              value={password}
              onChange={setPassword}
              placeholder="••••••••"
            />

            {error && (
              <p className="rounded-xl bg-danger/10 px-4 py-2.5 text-sm text-danger">
                {error}
              </p>
            )}

            <button
              disabled={busy}
              className="w-full rounded-xl py-3 font-semibold text-white shadow-maple-sm transition hover:brightness-105 disabled:opacity-60"
              style={{ background: "var(--accent)" }}
            >
              {busy ? t("login.processing") : t("login.signIn")}
            </button>
          </form>

          <div className="mt-5 flex items-center gap-3 text-xs text-ink-faint">
            <span className="h-px flex-1 bg-line" />
            {t("login.or")}
            <span className="h-px flex-1 bg-line" />
          </div>

          <div className="mt-4">
            <GoogleSignInButton onCredential={googleLogin} />
          </div>

          <p className="mt-6 text-center text-sm text-ink-faint">
            {t("login.adminIssued")}{" "}
            <button
              type="button"
              onClick={() => setRequesting(true)}
              className="font-semibold text-accent underline-offset-2 hover:underline"
            >
              {t("login.requestAccount")}
            </button>
          </p>
        </div>
      </div>

      {requesting && (
        <RequestAccountModal onClose={() => setRequesting(false)} />
      )}
    </div>
  );
}

/* FR-REQ-01: Form công khai gửi yêu cầu tài khoản cho Admin duyệt. */
function RequestAccountModal({ onClose }: { onClose: () => void }) {
  const { t } = useLang();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<Role>("USER");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [sentTo, setSentTo] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const send = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.post("/account-requests", {
        email: email.trim(),
        full_name: fullName.trim(),
        role,
        message: message.trim(),
      });
      setSentTo(email.trim());
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : t("req.failed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-3"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md overflow-hidden rounded-[22px] border border-line bg-bg shadow-maple"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 className="font-display text-lg font-bold text-ink">
            {t("req.title")}
          </h2>
          <button
            onClick={onClose}
            className="grid h-8 w-8 place-items-center rounded-lg text-ink-faint hover:bg-surface-2 hover:text-ink"
          >
            <IconClose size={18} />
          </button>
        </div>

        {sentTo ? (
          <div className="px-5 py-6">
            <p className="rounded-xl bg-emerald-500/10 px-4 py-3 text-sm text-emerald-600 dark:text-emerald-400">
              {t("req.sent", { email: sentTo })}
            </p>
            <button
              onClick={onClose}
              className="mt-4 w-full rounded-xl bg-accent py-2.5 font-semibold text-white transition hover:brightness-105"
            >
              OK
            </button>
          </div>
        ) : (
          <form onSubmit={send} className="space-y-3 px-5 py-5">
            <p className="text-sm text-ink-faint">{t("req.subtitle")}</p>
            <input
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder={t("req.fullName")}
              className="w-full rounded-xl border border-line bg-surface px-3.5 py-2.5 text-sm text-ink outline-none focus:border-accent placeholder:text-ink-faint"
            />
            <input
              required
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={t("req.email")}
              className="w-full rounded-xl border border-line bg-surface px-3.5 py-2.5 text-sm text-ink outline-none focus:border-accent placeholder:text-ink-faint"
            />
            <div className="flex items-center gap-3">
              <label className="text-sm font-medium text-ink-soft">
                {t("req.role")}
              </label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as Role)}
                className="flex-1 rounded-xl border border-line bg-surface px-3 py-2.5 text-sm text-ink outline-none focus:border-accent"
              >
                <option value="USER">{t("role.USER")}</option>
                <option value="LECTURER">{t("role.LECTURER")}</option>
              </select>
            </div>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder={t("req.message")}
              rows={3}
              className="w-full resize-none rounded-xl border border-line bg-surface px-3.5 py-2.5 text-sm text-ink outline-none focus:border-accent placeholder:text-ink-faint"
            />
            {error && (
              <p className="rounded-xl bg-danger/10 px-4 py-2.5 text-sm text-danger">
                {error}
              </p>
            )}
            <button
              disabled={busy || !fullName.trim() || !email.trim()}
              className="w-full rounded-xl bg-accent py-2.5 font-semibold text-white transition hover:brightness-105 disabled:opacity-50"
            >
              {busy ? t("req.sending") : t("req.send")}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium text-ink-soft">
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required
        className="w-full rounded-xl border border-line bg-surface px-4 py-2.5 text-sm text-ink outline-none transition focus:border-accent placeholder:text-ink-faint"
      />
    </div>
  );
}
