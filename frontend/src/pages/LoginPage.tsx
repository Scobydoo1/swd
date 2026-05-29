import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { useTheme } from "../theme/ThemeContext";
import { IconMaple, IconMoon, IconSun } from "../components/Icons";
import type { Role } from "../types";

export function LoginPage() {
  const { user, login, register } = useAuth();
  const { dark, toggle } = useTheme();
  const navigate = useNavigate();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState<Role>("USER");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "login") await login(email, password);
      else await register(email, password, fullName, role);
      navigate("/");
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Có lỗi xảy ra");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg p-4">
      <button
        onClick={toggle}
        className="absolute right-5 top-5 grid h-[38px] w-[38px] place-items-center rounded-[11px] text-ink-soft transition hover:bg-surface-2 hover:text-ink"
        title="Đổi giao diện"
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
            <p className="mt-3 text-white/80">
              Trợ lý học tập AI — hỏi đáp dựa trên tài liệu môn học, có trích dẫn
              nguồn chính xác.
            </p>
          </div>
          <ul className="space-y-3 text-sm text-white/85">
            <li className="flex items-center gap-2">📚 Quản lý tài liệu PDF / DOCX / Slide</li>
            <li className="flex items-center gap-2">🔍 Trả lời trong phạm vi tài liệu</li>
            <li className="flex items-center gap-2">💬 Lịch sử hội thoại theo phiên</li>
          </ul>
        </div>

        {/* Form panel */}
        <div className="p-8 sm:p-10">
          <h2 className="font-display text-2xl font-bold text-ink">
            {mode === "login" ? "Đăng nhập" : "Tạo tài khoản"}
          </h2>
          <p className="mt-1 text-sm text-ink-faint">
            {mode === "login" ? "Chào mừng quay lại!" : "Điền thông tin để bắt đầu."}
          </p>

          <form onSubmit={submit} className="mt-6 space-y-4">
            {mode === "register" && (
              <Field
                label="Họ và tên"
                value={fullName}
                onChange={setFullName}
                placeholder="Nguyễn Văn A"
              />
            )}
            <Field
              label="Email"
              type="email"
              value={email}
              onChange={setEmail}
              placeholder="you@example.com"
            />
            <Field
              label="Mật khẩu"
              type="password"
              value={password}
              onChange={setPassword}
              placeholder="••••••••"
            />
            {mode === "register" && (
              <div>
                <label className="mb-1.5 block text-sm font-medium text-ink-soft">
                  Vai trò
                </label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as Role)}
                  className="w-full rounded-xl border border-line bg-surface px-4 py-2.5 text-sm text-ink outline-none transition focus:border-accent"
                >
                  <option value="USER">Sinh viên</option>
                  <option value="LECTURER">Giảng viên</option>
                  <option value="ADMIN">Quản trị viên</option>
                </select>
              </div>
            )}

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
              {busy ? "Đang xử lý…" : mode === "login" ? "Đăng nhập" : "Đăng ký"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-ink-faint">
            {mode === "login" ? "Chưa có tài khoản? " : "Đã có tài khoản? "}
            <button
              onClick={() => {
                setMode(mode === "login" ? "register" : "login");
                setError("");
              }}
              className="font-semibold text-accent hover:underline"
            >
              {mode === "login" ? "Đăng ký ngay" : "Đăng nhập"}
            </button>
          </p>

          {mode === "login" && (
            <div className="mt-4 rounded-xl bg-surface-2 p-3 text-xs text-ink-faint">
              Demo: admin@demo.com · lecturer@demo.com · student@demo.com
              <br />
              Mật khẩu: admin123 / lecturer123 / student123
            </div>
          )}
        </div>
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
