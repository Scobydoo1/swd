import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { IconCheck, IconSidebar, IconSpark } from "../components/Icons";
import type { PlanOption, User } from "../types";

type Ctx = { openSidebar: () => void };

export function PricingPage() {
  const { openSidebar } = useOutletContext<Ctx>();
  const { user, refresh } = useAuth();
  const [plans, setPlans] = useState<PlanOption[]>([]);
  const [busy, setBusy] = useState<string | null>(null);

  const load = () => api.get<PlanOption[]>("/plans").then((r) => setPlans(r.data));
  useEffect(() => {
    load();
  }, []);

  const subscribe = async (id: string) => {
    setBusy(id);
    try {
      await api.post<User>("/subscriptions", { plan_id: id });
      await refresh?.();
      await load();
    } finally {
      setBusy(null);
    }
  };

  // Chỉ Sinh viên cần gói dịch vụ; Giảng viên & Admin được miễn.
  if (user && user.role !== "USER") {
    return (
      <div className="grid h-full place-items-center p-8 text-center">
        <div className="max-w-md">
          <div className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-accent/12 text-accent">
            <IconSpark size={28} />
          </div>
          <h1 className="font-display text-xl font-bold text-ink">
            Tài khoản của bạn không cần gói dịch vụ
          </h1>
          <p className="mt-2 text-sm text-ink-faint">
            Gói Free / Pro / Max chỉ dành cho sinh viên. Giảng viên và quản trị
            viên được sử dụng đầy đủ tính năng mà không cần đăng ký.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-4 sm:p-8">
      <div className="mx-auto max-w-5xl">
        <header className="mb-8">
          <div className="flex items-center gap-2">
            <button
              onClick={() => openSidebar()}
              className="grid h-[36px] w-[36px] flex-none place-items-center rounded-[10px] text-ink-soft transition hover:bg-surface-2 hover:text-ink lg:hidden"
              title="Mở thanh bên"
            >
              <IconSidebar size={19} />
            </button>
            <h1 className="font-display text-2xl font-bold text-ink">
              Gói dịch vụ
            </h1>
          </div>
          <p className="mt-1 text-sm text-ink-faint">
            Chọn gói phù hợp. Gói hiện tại của bạn:{" "}
            <span className="font-semibold text-accent">{user?.plan}</span>.
          </p>
        </header>

        <div className="grid gap-5 md:grid-cols-3">
          {plans.map((p) => (
            <div
              key={p.id}
              className={`relative flex flex-col rounded-[22px] border bg-surface p-6 shadow-maple-sm transition ${
                p.highlight
                  ? "border-accent/60 ring-1 ring-accent/30"
                  : "border-line"
              }`}
            >
              {p.highlight && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-accent px-3 py-1 text-xs font-semibold text-white">
                  Phổ biến
                </span>
              )}
              <div className="mb-1 flex items-center gap-2">
                <span className="text-accent">
                  <IconSpark size={20} />
                </span>
                <h3 className="font-display text-xl font-bold text-ink">
                  {p.name}
                </h3>
              </div>
              <p className="text-sm text-ink-faint">{p.tagline}</p>
              <div className="my-4 text-2xl font-bold text-ink">
                {p.price_label}
              </div>
              <ul className="mb-6 flex-1 space-y-2.5">
                {p.features.map((f, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-ink-soft">
                    <span className="mt-0.5 text-emerald-600">
                      <IconCheck size={16} />
                    </span>
                    {f}
                  </li>
                ))}
              </ul>
              <button
                disabled={p.current || busy === p.id}
                onClick={() => subscribe(p.id)}
                className={`rounded-xl py-2.5 text-sm font-semibold transition disabled:cursor-default ${
                  p.current
                    ? "border border-line bg-surface-2 text-ink-faint"
                    : "bg-accent text-white hover:brightness-105"
                }`}
              >
                {p.current
                  ? "Gói hiện tại"
                  : busy === p.id
                    ? "Đang xử lý…"
                    : p.price === 0
                      ? "Dùng miễn phí"
                      : "Nâng cấp"}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
