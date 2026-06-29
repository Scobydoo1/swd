import { useCallback, useEffect, useState } from "react";
import { useNavigate, useOutletContext, useParams } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { useLang } from "../i18n/LanguageContext";
import { formatDateTimeVN } from "../lib/datetime";
import {
  IconChart,
  IconChevron,
  IconClose,
  IconDownload,
  IconFile,
  IconPlus,
  IconQuiz,
  IconRoom,
  IconSidebar,
  IconTrash,
  IconUserPlus,
  IconUsers,
} from "../components/Icons";
import {
  AttemptsModal,
  Overlay,
  TakeQuizModal,
} from "../components/quiz/QuizModals";
import type {
  QuizDetail,
  QuizListItem,
  RoomDetail,
  RoomGradeRow,
  RoomStudent,
} from "../types";

type Ctx = { openSidebar: () => void };

function quizClosed(q: QuizListItem): boolean {
  return !!q.closes_at && new Date(q.closes_at + "Z").getTime() < Date.now();
}
function quizNotOpen(q: QuizListItem): boolean {
  return !!q.opens_at && new Date(q.opens_at + "Z").getTime() > Date.now();
}

// FR-ROOM-03: Lớp học online — bảng tin, quiz (mật khẩu/hạn), bảng điểm, tài liệu.
export function RoomDetailPage() {
  const { openSidebar } = useOutletContext<Ctx>();
  const { id } = useParams();
  const { user } = useAuth();
  const { t } = useLang();
  const navigate = useNavigate();

  const [room, setRoom] = useState<RoomDetail | null>(null);
  const [inviting, setInviting] = useState(false);
  const [taking, setTaking] = useState<QuizDetail | null>(null);
  const [viewingResults, setViewingResults] = useState<QuizListItem | null>(
    null
  );
  const [pwPrompt, setPwPrompt] = useState<QuizListItem | null>(null);
  const [showGrades, setShowGrades] = useState(false);
  const [annText, setAnnText] = useState("");
  const [dlError, setDlError] = useState<string | null>(null);

  const canManage =
    !!user &&
    !!room &&
    (user.role === "ADMIN" ||
      (user.role === "LECTURER" && room.created_by === user.id));

  const load = useCallback(() => {
    api
      .get<RoomDetail>(`/rooms/${id}`)
      .then((r) => setRoom(r.data))
      .catch(() => navigate("/rooms", { replace: true }));
  }, [id, navigate]);
  useEffect(() => {
    load();
  }, [load]);

  const removeMember = async (userId: number, name: string) => {
    if (!confirm(t("rooms.removeMemberConfirm", { name }))) return;
    await api.delete(`/rooms/${id}/members/${userId}`);
    load();
  };

  // FR-ROOM-03: tải nguyên bản tài liệu học tập (blob -> tải về máy).
  const downloadDoc = async (docId: number, filename: string) => {
    setDlError(null);
    try {
      const res = await api.get(`/rooms/${id}/documents/${docId}/download`, {
        responseType: "blob",
      });
      const url = URL.createObjectURL(res.data as Blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      setDlError(t("rooms.downloadFailed"));
    }
  };

  // Mở quiz: nếu có mật khẩu và là Sinh viên thì hỏi mật khẩu trước.
  const tryOpen = (q: QuizListItem) => {
    if (q.has_password && !canManage) setPwPrompt(q);
    else openTake(q);
  };

  const openTake = async (q: QuizListItem, password?: string) => {
    const { data } = await api.get<QuizDetail>(`/quizzes/${q.id}`, {
      params: password ? { password } : undefined,
    });
    setTaking(data);
    setPwPrompt(null);
  };

  const postAnnouncement = async () => {
    if (!annText.trim()) return;
    await api.post(`/rooms/${id}/announcements`, { content: annText.trim() });
    setAnnText("");
    load();
  };

  const deleteAnnouncement = async (annId: number) => {
    if (!confirm(t("rooms.deleteAnnouncementConfirm"))) return;
    await api.delete(`/rooms/${id}/announcements/${annId}`);
    load();
  };

  if (!room)
    return (
      <div className="flex h-full items-center justify-center text-ink-faint">
        …
      </div>
    );

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
            <button
              onClick={() => navigate("/rooms")}
              className="flex items-center gap-1 rounded-lg px-2 py-1 text-sm font-medium text-ink-faint transition hover:bg-surface-2 hover:text-ink"
            >
              <span className="rotate-180">
                <IconChevron size={15} />
              </span>
              {t("rooms.back")}
            </button>
          </div>
          <div className="mt-3 flex items-start gap-3">
            <span className="grid h-12 w-12 flex-none place-items-center rounded-2xl bg-accent/10 text-accent">
              <IconRoom size={24} />
            </span>
            <div className="min-w-0 flex-1">
              <h1 className="font-display text-2xl font-bold text-ink">
                {room.name}
              </h1>
              <p className="text-sm text-ink-faint">
                {t("rooms.course")} {room.course_name}
                {room.description ? ` — ${room.description}` : ""}
              </p>
            </div>
            {canManage && (
              <button
                onClick={() => setShowGrades(true)}
                className="flex flex-none items-center gap-1.5 rounded-xl border border-line bg-surface px-3 py-2 text-sm font-semibold text-ink-soft transition hover:border-accent/60 hover:text-accent"
              >
                <IconChart size={16} /> {t("rooms.grades")}
              </button>
            )}
          </div>
        </header>

        {/* Bảng tin / thông báo */}
        <section className="mb-6 rounded-[18px] border border-line bg-surface p-5 shadow-maple-sm">
          <h2 className="mb-3 flex items-center gap-2 font-semibold text-ink">
            <span className="text-accent">
              <IconRoom size={18} />
            </span>
            {t("rooms.announcements")} ({room.announcements.length})
          </h2>
          {canManage && (
            <div className="mb-3 flex gap-2">
              <textarea
                value={annText}
                onChange={(e) => setAnnText(e.target.value)}
                placeholder={t("rooms.announcementPlaceholder")}
                rows={2}
                className="flex-1 resize-none rounded-xl border border-line bg-surface px-3.5 py-2 text-sm text-ink outline-none focus:border-accent"
              />
              <button
                onClick={postAnnouncement}
                disabled={!annText.trim()}
                className="flex-none rounded-xl bg-accent px-4 text-sm font-semibold text-white transition hover:brightness-105 disabled:opacity-50"
              >
                {t("rooms.post")}
              </button>
            </div>
          )}
          {room.announcements.length === 0 ? (
            <p className="rounded-xl border border-dashed border-line p-4 text-center text-sm text-ink-faint">
              {t("rooms.noAnnouncements")}
            </p>
          ) : (
            <div className="flex flex-col gap-2">
              {room.announcements.map((a) => (
                <div
                  key={a.id}
                  className="flex items-start gap-3 rounded-xl border border-line bg-surface-2/40 px-3.5 py-2.5"
                >
                  <div className="min-w-0 flex-1">
                    <p className="whitespace-pre-wrap text-sm text-ink">
                      {a.content}
                    </p>
                    <p className="mt-1 text-xs text-ink-faint">
                      {a.author_name ?? "—"} · {formatDateTimeVN(a.created_at)}
                    </p>
                  </div>
                  {canManage && (
                    <button
                      onClick={() => deleteAnnouncement(a.id)}
                      className="grid h-8 w-8 flex-none place-items-center rounded-lg text-ink-faint transition hover:bg-danger/10 hover:text-danger"
                      title={t("common.delete")}
                    >
                      <IconTrash size={15} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Thành viên */}
        <section className="mb-6 rounded-[18px] border border-line bg-surface p-5 shadow-maple-sm">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="flex items-center gap-2 font-semibold text-ink">
              <span className="text-accent">
                <IconUsers size={18} />
              </span>
              {t("rooms.membersTitle")} ({room.members.length})
            </h2>
            {canManage && (
              <button
                onClick={() => setInviting(true)}
                className="flex items-center gap-1.5 rounded-xl bg-accent px-3 py-2 text-sm font-semibold text-white shadow-maple-sm transition hover:brightness-105"
              >
                <IconUserPlus size={16} /> {t("rooms.invite")}
              </button>
            )}
          </div>
          {room.members.length === 0 ? (
            <p className="rounded-xl border border-dashed border-line p-4 text-center text-sm text-ink-faint">
              {t("rooms.noMembers")}
            </p>
          ) : (
            <div className="flex flex-col">
              {room.members.map((m) => (
                <div
                  key={m.user_id}
                  className="flex items-center gap-3 border-t border-line-soft py-2.5 first:border-t-0"
                >
                  <div className="avatar avatar-user sm">
                    {m.full_name.charAt(0)}
                  </div>
                  <div className="min-w-0 flex-1 leading-tight">
                    <div className="truncate text-sm font-medium text-ink">
                      {m.full_name}
                    </div>
                    <div className="truncate text-xs text-ink-faint">
                      {m.email}
                    </div>
                  </div>
                  {canManage && (
                    <button
                      onClick={() => removeMember(m.user_id, m.full_name)}
                      className="grid h-8 w-8 flex-none place-items-center rounded-lg text-ink-faint transition hover:bg-danger/10 hover:text-danger"
                      title={t("common.delete")}
                    >
                      <IconTrash size={15} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Quiz của lớp */}
        <section className="mb-6 rounded-[18px] border border-line bg-surface p-5 shadow-maple-sm">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="flex items-center gap-2 font-semibold text-ink">
              <span className="text-accent">
                <IconQuiz size={18} />
              </span>
              {t("rooms.quizzesTitle")} ({room.quizzes.length})
            </h2>
            {canManage && (
              <button
                onClick={() => navigate("/quizzes")}
                className="flex items-center gap-1.5 rounded-xl border border-line bg-surface px-3 py-2 text-sm font-semibold text-accent transition hover:border-accent/60"
              >
                <IconPlus size={15} /> {t("rooms.createQuiz")}
              </button>
            )}
          </div>
          {room.quizzes.length === 0 ? (
            <p className="rounded-xl border border-dashed border-line p-4 text-center text-sm text-ink-faint">
              {t("rooms.noQuizzes")}
            </p>
          ) : (
            <div className="flex flex-col gap-2">
              {room.quizzes.map((q) => {
                const closed = quizClosed(q);
                const notOpen = quizNotOpen(q);
                const blocked = !canManage && (closed || notOpen);
                return (
                  <div
                    key={q.id}
                    className="flex flex-wrap items-center gap-3 rounded-xl border border-line bg-surface-2/40 px-3.5 py-2.5"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-semibold text-ink">
                        {q.title}
                      </div>
                      <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-ink-faint">
                        <span>{t("quiz.numQuestions", { n: q.num_questions })}</span>
                        {q.has_password && <span>· 🔒 {t("quiz.locked")}</span>}
                        {closed && (
                          <span className="text-danger">· {t("quiz.closed")}</span>
                        )}
                        {notOpen && <span>· {t("quiz.notOpen")}</span>}
                        {q.closes_at && !closed && (
                          <span>
                            · {t("quiz.due", { time: formatDateTimeVN(q.closes_at) })}
                          </span>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => tryOpen(q)}
                      disabled={blocked}
                      className="flex-none rounded-lg border border-line bg-surface px-3 py-1.5 text-xs font-semibold text-accent transition hover:border-accent/60 disabled:opacity-40"
                    >
                      {canManage ? t("quiz.viewTry") : t("quiz.take")}
                    </button>
                    {canManage && (
                      <button
                        onClick={() => setViewingResults(q)}
                        className="flex flex-none items-center gap-1 rounded-lg border border-line bg-surface px-3 py-1.5 text-xs font-semibold text-ink-soft transition hover:border-accent/60 hover:text-accent"
                      >
                        <IconChart size={14} /> {t("quiz.results")}
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* Tài liệu học tập của môn */}
        <section className="rounded-[18px] border border-line bg-surface p-5 shadow-maple-sm">
          <h2 className="mb-3 flex items-center gap-2 font-semibold text-ink">
            <span className="text-accent">
              <IconFile size={18} />
            </span>
            {t("rooms.documentsTitle")} ({room.documents.length})
          </h2>
          {dlError && (
            <p className="mb-2 rounded-xl bg-danger/10 px-4 py-2.5 text-sm text-danger">
              {dlError}
            </p>
          )}
          {room.documents.length === 0 ? (
            <p className="rounded-xl border border-dashed border-line p-4 text-center text-sm text-ink-faint">
              {t("rooms.noDocs")}
            </p>
          ) : (
            <div className="flex flex-col gap-2">
              {room.documents.map((d) => (
                <div
                  key={d.id}
                  className="flex items-center gap-3 rounded-xl border border-line bg-surface-2/40 px-3.5 py-2.5"
                >
                  <span className="grid h-9 w-9 flex-none place-items-center rounded-lg bg-surface text-accent">
                    <IconFile size={17} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium text-ink">
                      {d.filename}
                    </div>
                    <div className="text-xs text-ink-faint">{d.file_type}</div>
                  </div>
                  <span
                    className={`flex-none rounded-full px-2.5 py-1 text-[11px] font-bold ${
                      d.status === "INDEXED"
                        ? "bg-emerald-500/10 text-emerald-600"
                        : d.status === "PROCESSING"
                          ? "bg-amber-500/10 text-amber-600"
                          : "bg-danger/10 text-danger"
                    }`}
                  >
                    {t(`docs.status${d.status}`)}
                  </span>
                  {d.has_file && (
                    <button
                      onClick={() => downloadDoc(d.id, d.filename)}
                      className="grid h-9 w-9 flex-none place-items-center rounded-lg text-ink-faint transition hover:bg-surface hover:text-accent"
                      title={t("rooms.download")}
                    >
                      <IconDownload size={17} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      {inviting && (
        <InviteModal
          roomId={room.id}
          existing={room.members.map((m) => m.user_id)}
          onClose={() => setInviting(false)}
          onInvited={() => {
            setInviting(false);
            load();
          }}
        />
      )}
      {pwPrompt && (
        <PasswordPrompt
          quiz={pwPrompt}
          onClose={() => setPwPrompt(null)}
          onUnlock={(pwd) => openTake(pwPrompt, pwd)}
        />
      )}
      {taking && (
        <TakeQuizModal quiz={taking} onClose={() => setTaking(null)} />
      )}
      {viewingResults && (
        <AttemptsModal
          quizId={viewingResults.id}
          quizTitle={viewingResults.title}
          onClose={() => setViewingResults(null)}
        />
      )}
      {showGrades && (
        <GradeOverviewModal
          roomId={room.id}
          roomName={room.name}
          onClose={() => setShowGrades(false)}
        />
      )}
    </div>
  );
}

/* ---------------- Password prompt (FR-QZ) ---------------- */
function PasswordPrompt({
  quiz,
  onClose,
  onUnlock,
}: {
  quiz: QuizListItem;
  onClose: () => void;
  onUnlock: (pwd: string) => Promise<void>;
}) {
  const { t } = useLang();
  const [pwd, setPwd] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setBusy(true);
    setError("");
    try {
      await onUnlock(pwd);
    } catch (e: any) {
      setError(e.response?.data?.detail ?? t("quiz.wrongPassword"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Overlay onClose={onClose}>
      <div className="flex items-center justify-between border-b border-line px-5 py-4">
        <h2 className="font-display text-lg font-bold text-ink">{quiz.title}</h2>
        <button
          onClick={onClose}
          className="grid h-8 w-8 place-items-center rounded-lg text-ink-faint hover:bg-surface-2 hover:text-ink"
        >
          <IconClose size={18} />
        </button>
      </div>
      <div className="px-5 py-5">
        <p className="mb-2 text-sm text-ink-soft">{t("quiz.enterPassword")}</p>
        <input
          type="password"
          value={pwd}
          autoFocus
          onChange={(e) => setPwd(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          className="w-full rounded-xl border border-line bg-surface px-3.5 py-2.5 text-sm text-ink outline-none focus:border-accent"
        />
        {error && (
          <p className="mt-2 rounded-lg bg-danger/10 px-3 py-2 text-xs text-danger">
            {error}
          </p>
        )}
        <button
          onClick={submit}
          disabled={busy || !pwd}
          className="mt-3 w-full rounded-xl bg-accent py-2.5 font-semibold text-white transition hover:brightness-105 disabled:opacity-50"
        >
          {t("quiz.unlock")}
        </button>
      </div>
    </Overlay>
  );
}

/* ---------------- Class grade overview (FR-ROOM-06) ---------------- */
function GradeOverviewModal({
  roomId,
  roomName,
  onClose,
}: {
  roomId: number;
  roomName: string;
  onClose: () => void;
}) {
  const { t } = useLang();
  const [rows, setRows] = useState<RoomGradeRow[] | null>(null);

  useEffect(() => {
    api
      .get<RoomGradeRow[]>(`/rooms/${roomId}/grades`)
      .then((r) => setRows(r.data))
      .catch(() => setRows([]));
  }, [roomId]);

  return (
    <Overlay onClose={onClose}>
      <div className="flex items-center justify-between border-b border-line px-5 py-4">
        <h2 className="font-display text-lg font-bold text-ink">
          {t("rooms.gradesTitle", { name: roomName })}
        </h2>
        <button
          onClick={onClose}
          className="grid h-8 w-8 place-items-center rounded-lg text-ink-faint hover:bg-surface-2 hover:text-ink"
        >
          <IconClose size={18} />
        </button>
      </div>
      <div className="max-h-[60vh] overflow-y-auto px-5 py-5">
        {rows === null ? (
          <p className="text-sm text-ink-faint">…</p>
        ) : rows.length === 0 ? (
          <p className="rounded-xl border border-dashed border-line p-6 text-center text-sm text-ink-faint">
            {t("rooms.noGrades")}
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wider text-ink-faint">
                <th className="pb-2 font-semibold">{t("quiz.colStudent")}</th>
                <th className="pb-2 font-semibold">{t("rooms.colQuiz")}</th>
                <th className="pb-2 font-semibold">{t("quiz.colScore")}</th>
                <th className="pb-2 font-semibold">{t("quiz.colTime")}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} className="border-t border-line-soft">
                  <td className="py-2.5">
                    <div className="font-medium text-ink">
                      {r.student_name ?? t("quiz.deletedUser")}
                    </div>
                    {r.student_email && (
                      <div className="text-xs text-ink-faint">
                        {r.student_email}
                      </div>
                    )}
                  </td>
                  <td className="py-2.5 text-ink-soft">{r.quiz_title}</td>
                  <td className="py-2.5">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-bold ${
                        r.score >= 50
                          ? "bg-emerald-500/10 text-emerald-600"
                          : "bg-danger/10 text-danger"
                      }`}
                    >
                      {r.score}%
                    </span>
                  </td>
                  <td className="py-2.5 text-ink-faint">
                    {formatDateTimeVN(r.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Overlay>
  );
}

/* ---------------- Invite student (FR-ROOM-04) ---------------- */
function InviteModal({
  roomId,
  existing,
  onClose,
  onInvited,
}: {
  roomId: number;
  existing: number[];
  onClose: () => void;
  onInvited: () => void;
}) {
  const { t } = useLang();
  const [students, setStudents] = useState<RoomStudent[]>([]);
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get<RoomStudent[]>("/rooms/students").then((r) => setStudents(r.data));
  }, []);

  const candidates = students.filter((s) => !existing.includes(s.id));

  const invite = async (target: string) => {
    setBusy(true);
    setError("");
    try {
      await api.post(`/rooms/${roomId}/members`, { email: target });
      onInvited();
    } catch (e: any) {
      setError(e.response?.data?.detail ?? t("rooms.inviteFailed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Overlay onClose={onClose}>
      <div className="flex items-center justify-between border-b border-line px-5 py-4">
        <h2 className="font-display text-lg font-bold text-ink">
          {t("rooms.inviteTitle")}
        </h2>
        <button
          onClick={onClose}
          className="grid h-8 w-8 place-items-center rounded-lg text-ink-faint hover:bg-surface-2 hover:text-ink"
        >
          <IconClose size={18} />
        </button>
      </div>

      <div className="px-5 py-5">
        <div className="flex gap-2">
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={t("rooms.inviteEmail")}
            type="email"
            className="flex-1 rounded-xl border border-line bg-surface px-3.5 py-2.5 text-sm text-ink outline-none focus:border-accent"
          />
          <button
            onClick={() => invite(email.trim())}
            disabled={!email.trim() || busy}
            className="flex-none rounded-xl bg-accent px-4 py-2.5 text-sm font-semibold text-white transition hover:brightness-105 disabled:opacity-50"
          >
            {t("rooms.invite")}
          </button>
        </div>

        {candidates.length > 0 && (
          <>
            <p className="mb-2 mt-4 text-xs font-semibold uppercase tracking-wider text-ink-faint">
              {t("rooms.invitePick")}
            </p>
            <div className="flex max-h-[38vh] flex-col gap-1 overflow-y-auto">
              {candidates.map((s) => (
                <button
                  key={s.id}
                  disabled={busy}
                  onClick={() => invite(s.email)}
                  className="flex items-center gap-3 rounded-xl px-2.5 py-2 text-left transition hover:bg-surface-2"
                >
                  <div className="avatar avatar-user sm">
                    {s.full_name.charAt(0)}
                  </div>
                  <div className="min-w-0 flex-1 leading-tight">
                    <div className="truncate text-sm font-medium text-ink">
                      {s.full_name}
                    </div>
                    <div className="truncate text-xs text-ink-faint">
                      {s.email}
                    </div>
                  </div>
                  <span className="flex-none text-accent">
                    <IconUserPlus size={16} />
                  </span>
                </button>
              ))}
            </div>
          </>
        )}

        {error && (
          <p className="mt-3 rounded-xl bg-danger/10 px-4 py-2.5 text-sm text-danger">
            {error}
          </p>
        )}
      </div>
    </Overlay>
  );
}
