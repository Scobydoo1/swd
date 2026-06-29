import { useRef, useState } from "react";
import { api } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import { useLang } from "../../i18n/LanguageContext";
import { IconClose } from "../Icons";

// FR-USR: Mọi người dùng tự sửa hồ sơ (tên + ảnh) và đổi mật khẩu của mình.
// Ảnh được resize phía client (~256px) rồi gửi dạng data URI để DB không phình.
async function fileToAvatar(file: File): Promise<string> {
  const dataUrl = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
  const img = await new Promise<HTMLImageElement>((resolve, reject) => {
    const i = new Image();
    i.onload = () => resolve(i);
    i.onerror = reject;
    i.src = dataUrl;
  });
  const max = 256;
  const scale = Math.min(1, max / Math.max(img.width, img.height));
  const w = Math.round(img.width * scale);
  const h = Math.round(img.height * scale);
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d");
  if (!ctx) return dataUrl;
  ctx.drawImage(img, 0, 0, w, h);
  return canvas.toDataURL("image/jpeg", 0.85);
}

export function ProfileSettingsModal({ onClose }: { onClose: () => void }) {
  const { user, refresh } = useAuth();
  const { t } = useLang();
  const fileRef = useRef<HTMLInputElement>(null);

  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [avatar, setAvatar] = useState<string | null>(user?.avatar_url ?? null);
  const [avatarChanged, setAvatarChanged] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const [curPw, setCurPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [pwBusy, setPwBusy] = useState(false);
  const [pwMsg, setPwMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const pickPhoto = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setMsg({ ok: false, text: t("profile.invalidImage") });
      return;
    }
    try {
      const data = await fileToAvatar(file);
      if (data.length > 1_500_000) {
        setMsg({ ok: false, text: t("profile.imageTooLarge") });
        return;
      }
      setAvatar(data);
      setAvatarChanged(true);
      setMsg(null);
    } catch {
      setMsg({ ok: false, text: t("profile.invalidImage") });
    }
  };

  const removePhoto = () => {
    setAvatar(null);
    setAvatarChanged(true);
  };

  const saveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    try {
      const payload: { full_name: string; avatar_url?: string | null } = {
        full_name: fullName.trim(),
      };
      if (avatarChanged) payload.avatar_url = avatar;
      await api.patch("/users/me", payload);
      await refresh();
      setAvatarChanged(false);
      setMsg({ ok: true, text: t("profile.saved") });
    } catch (err: any) {
      setMsg({ ok: false, text: err.response?.data?.detail ?? t("common.error") });
    } finally {
      setBusy(false);
    }
  };

  const changePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwMsg(null);
    if (newPw.length < 6) {
      setPwMsg({ ok: false, text: t("profile.passwordTooShort") });
      return;
    }
    if (newPw !== confirmPw) {
      setPwMsg({ ok: false, text: t("profile.passwordMismatch") });
      return;
    }
    setPwBusy(true);
    try {
      await api.patch("/users/me/password", {
        current_password: curPw,
        new_password: newPw,
      });
      setCurPw("");
      setNewPw("");
      setConfirmPw("");
      setPwMsg({ ok: true, text: t("profile.passwordChanged") });
    } catch (err: any) {
      setPwMsg({
        ok: false,
        text: err.response?.data?.detail ?? t("common.error"),
      });
    } finally {
      setPwBusy(false);
    }
  };

  const inputCls =
    "w-full rounded-xl border border-line bg-surface px-3.5 py-2.5 text-sm text-ink outline-none focus:border-accent placeholder:text-ink-faint";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-3"
      onClick={onClose}
    >
      <div
        className="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-[22px] border border-line bg-bg shadow-maple"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 className="font-display text-lg font-bold text-ink">
            {t("profile.title")}
          </h2>
          <button
            onClick={onClose}
            className="grid h-8 w-8 place-items-center rounded-lg text-ink-faint hover:bg-surface-2 hover:text-ink"
          >
            <IconClose size={18} />
          </button>
        </div>

        {/* Hồ sơ: ảnh + tên */}
        <form onSubmit={saveProfile} className="space-y-4 px-5 py-5">
          <div className="flex items-center gap-4">
            {avatar ? (
              <img
                src={avatar}
                alt=""
                className="h-20 w-20 flex-none rounded-full object-cover"
              />
            ) : (
              <div className="avatar avatar-user grid h-20 w-20 flex-none place-items-center text-2xl">
                {fullName.charAt(0) || user?.full_name?.charAt(0) || "?"}
              </div>
            )}
            <div className="flex flex-col gap-2">
              <input
                ref={fileRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={pickPhoto}
              />
              <button
                type="button"
                onClick={() => fileRef.current?.click()}
                className="rounded-xl border border-line bg-surface px-3.5 py-2 text-sm font-medium text-ink transition hover:bg-surface-2"
              >
                {t("profile.changePhoto")}
              </button>
              {avatar && (
                <button
                  type="button"
                  onClick={removePhoto}
                  className="text-sm font-medium text-ink-faint transition hover:text-danger"
                >
                  {t("profile.removePhoto")}
                </button>
              )}
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-ink-soft">
              {t("profile.fullName")}
            </label>
            <input
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className={inputCls}
              required
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-ink-soft">
              {t("profile.email")}
            </label>
            <input
              value={user?.email ?? ""}
              disabled
              className={`${inputCls} cursor-not-allowed opacity-60`}
            />
          </div>

          {msg && (
            <p
              className={`rounded-xl px-4 py-2.5 text-sm ${
                msg.ok
                  ? "bg-emerald-500/10 text-emerald-600"
                  : "bg-danger/10 text-danger"
              }`}
            >
              {msg.text}
            </p>
          )}

          <button
            disabled={busy || !fullName.trim()}
            className="w-full rounded-xl bg-accent py-2.5 font-semibold text-white transition hover:brightness-105 disabled:opacity-50"
          >
            {t("profile.save")}
          </button>
        </form>

        {/* Đổi mật khẩu */}
        <form
          onSubmit={changePassword}
          className="space-y-3 border-t border-line px-5 py-5"
        >
          <h3 className="font-semibold text-ink">{t("profile.passwordSection")}</h3>
          <input
            type="password"
            value={curPw}
            onChange={(e) => setCurPw(e.target.value)}
            placeholder={t("profile.currentPassword")}
            className={inputCls}
            required
            autoComplete="current-password"
          />
          <input
            type="password"
            value={newPw}
            onChange={(e) => setNewPw(e.target.value)}
            placeholder={t("profile.newPassword")}
            className={inputCls}
            required
            autoComplete="new-password"
          />
          <input
            type="password"
            value={confirmPw}
            onChange={(e) => setConfirmPw(e.target.value)}
            placeholder={t("profile.confirmPassword")}
            className={inputCls}
            required
            autoComplete="new-password"
          />
          {pwMsg && (
            <p
              className={`rounded-xl px-4 py-2.5 text-sm ${
                pwMsg.ok
                  ? "bg-emerald-500/10 text-emerald-600"
                  : "bg-danger/10 text-danger"
              }`}
            >
              {pwMsg.text}
            </p>
          )}
          <button
            disabled={pwBusy || !curPw || !newPw || !confirmPw}
            className="w-full rounded-xl border border-line bg-surface py-2.5 font-semibold text-ink transition hover:bg-surface-2 disabled:opacity-50"
          >
            {t("profile.changePassword")}
          </button>
        </form>
      </div>
    </div>
  );
}
