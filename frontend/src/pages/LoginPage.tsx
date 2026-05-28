import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import type { Role } from "../types";

export function LoginPage() {
  const { user, login, register } = useAuth();
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
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-600 via-brand-700 to-indigo-900 p-4">
      <div className="grid w-full max-w-4xl overflow-hidden rounded-3xl bg-white shadow-2xl md:grid-cols-2">
        <div className="hidden flex-col justify-between bg-gradient-to-br from-brand-500 to-brand-800 p-10 text-white md:flex">
          <div>
            <div className="grid h-14 w-14 place-items-center rounded-2xl bg-white/20 text-2xl font-extrabold backdrop-blur">
              E
            </div>
            <h1 className="mt-8 text-3xl font-extrabold leading-tight">
              EduRAG
            </h1>
            <p className="mt-3 text-brand-100">
              Trợ lý học tập AI — hỏi đáp dựa trên tài liệu môn học, có trích
              dẫn nguồn chính xác.
            </p>
          </div>
          <ul className="space-y-3 text-sm text-brand-100">
            <li className="flex items-center gap-2">📚 Quản lý tài liệu PDF / DOCX / Slide</li>
            <li className="flex items-center gap-2">🔍 Trả lời trong phạm vi tài liệu</li>
            <li className="flex items-center gap-2">💬 Lịch sử hội thoại theo phiên</li>
          </ul>
        </div>

        <div className="p-8 sm:p-10">
          <h2 className="text-2xl font-extrabold text-slate-800">
            {mode === "login" ? "Đăng nhập" : "Tạo tài khoản"}
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            {mode === "login"
              ? "Chào mừng quay lại!"
              : "Điền thông tin để bắt đầu."}
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
                <label className="mb-1.5 block text-sm font-medium text-slate-600">
                  Vai trò
                </label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as Role)}
                  className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-200"
                >
                  <option value="USER">Sinh viên</option>
                  <option value="LECTURER">Giảng viên</option>
                  <option value="ADMIN">Quản trị viên</option>
                </select>
              </div>
            )}

            {error && (
              <p className="rounded-xl bg-rose-50 px-4 py-2.5 text-sm text-rose-600">
                {error}
              </p>
            )}

            <button
              disabled={busy}
              className="w-full rounded-xl bg-brand-600 py-3 font-semibold text-white shadow-lg shadow-brand-600/30 transition hover:bg-brand-700 disabled:opacity-60"
            >
              {busy ? "Đang xử lý…" : mode === "login" ? "Đăng nhập" : "Đăng ký"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-400">
            {mode === "login" ? "Chưa có tài khoản? " : "Đã có tài khoản? "}
            <button
              onClick={() => {
                setMode(mode === "login" ? "register" : "login");
                setError("");
              }}
              className="font-semibold text-brand-600 hover:underline"
            >
              {mode === "login" ? "Đăng ký ngay" : "Đăng nhập"}
            </button>
          </p>

          {mode === "login" && (
            <div className="mt-4 rounded-xl bg-slate-50 p-3 text-xs text-slate-400">
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
      <label className="mb-1.5 block text-sm font-medium text-slate-600">
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required
        className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-200"
      />
    </div>
  );
}
