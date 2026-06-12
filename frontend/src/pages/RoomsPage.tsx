import { useEffect, useState } from "react";
import { useNavigate, useOutletContext } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { useLang } from "../i18n/LanguageContext";
import {
  IconClose,
  IconPlus,
  IconRoom,
  IconSidebar,
  IconTrash,
} from "../components/Icons";
import { Overlay } from "../components/quiz/QuizModals";
import type { Course, Room } from "../types";

type Ctx = { openSidebar: () => void };

// FR-ROOM: Danh sách phòng học — Lecturer/Admin quản lý, Sinh viên xem phòng
// mình được mời.
export function RoomsPage() {
  const { openSidebar } = useOutletContext<Ctx>();
  const { user } = useAuth();
  const { t } = useLang();
  const navigate = useNavigate();
  const canManage = user?.role === "ADMIN" || user?.role === "LECTURER";

  const [rooms, setRooms] = useState<Room[]>([]);
  const [creating, setCreating] = useState(false);

  const load = () => api.get<Room[]>("/rooms").then((r) => setRooms(r.data));
  useEffect(() => {
    load();
  }, []);

  const remove = async (e: React.MouseEvent, room: Room) => {
    e.stopPropagation();
    if (!confirm(t("rooms.deleteConfirm", { name: room.name }))) return;
    await api.delete(`/rooms/${room.id}`);
    load();
  };

  return (
    <div className="h-full overflow-y-auto p-4 sm:p-8">
      <div className="mx-auto max-w-4xl">
        <header className="mb-6 flex items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => openSidebar()}
                className="grid h-[36px] w-[36px] flex-none place-items-center rounded-[10px] text-ink-soft transition hover:bg-surface-2 hover:text-ink lg:hidden"
                title={t("common.openSidebar")}
              >
                <IconSidebar size={19} />
              </button>
              <h1 className="font-display text-2xl font-bold text-ink">
                {t("nav.rooms")}
              </h1>
            </div>
            <p className="mt-1 text-sm text-ink-faint">
              {canManage ? t("rooms.subtitleManage") : t("rooms.subtitleJoin")}
            </p>
          </div>
          {canManage && (
            <button
              onClick={() => setCreating(true)}
              className="flex flex-none items-center gap-2 rounded-xl bg-accent px-3.5 py-2.5 text-sm font-semibold text-white shadow-maple-sm transition hover:brightness-105"
            >
              <IconPlus size={17} /> {t("rooms.create")}
            </button>
          )}
        </header>

        {rooms.length === 0 ? (
          <div className="rounded-[20px] border border-dashed border-line bg-surface p-10 text-center text-ink-faint">
            <div className="mx-auto mb-3 grid h-14 w-14 place-items-center rounded-2xl bg-surface-2 text-accent">
              <IconRoom size={26} />
            </div>
            {canManage ? t("rooms.empty") : t("rooms.emptyStudent")}
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {rooms.map((room) => (
              <div
                key={room.id}
                onClick={() => navigate(`/rooms/${room.id}`)}
                className="flex cursor-pointer flex-col rounded-[18px] border border-line bg-surface p-5 shadow-maple-sm transition hover:border-accent/40 hover:-translate-y-px"
              >
                <div className="flex items-start gap-3">
                  <span className="grid h-10 w-10 flex-none place-items-center rounded-xl bg-surface-2 text-accent">
                    <IconRoom size={20} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <h3 className="truncate font-semibold text-ink">
                      {room.name}
                    </h3>
                    <p className="truncate text-xs text-ink-faint">
                      {room.course_name}
                    </p>
                  </div>
                  {canManage && (
                    <button
                      onClick={(e) => remove(e, room)}
                      className="grid h-8 w-8 flex-none place-items-center rounded-lg text-ink-faint transition hover:bg-danger/10 hover:text-danger"
                      title={t("common.delete")}
                    >
                      <IconTrash size={16} />
                    </button>
                  )}
                </div>
                {room.description && (
                  <p className="mt-2 line-clamp-2 text-sm text-ink-soft">
                    {room.description}
                  </p>
                )}
                <div className="mt-3 flex gap-2 text-xs font-semibold text-ink-faint">
                  <span className="rounded-full bg-surface-2 px-2.5 py-1">
                    {t("rooms.members", { n: room.num_members })}
                  </span>
                  <span className="rounded-full bg-surface-2 px-2.5 py-1">
                    {t("rooms.numQuizzes", { n: room.num_quizzes })}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {creating && (
        <CreateRoomModal
          onClose={() => setCreating(false)}
          onCreated={() => {
            setCreating(false);
            load();
          }}
        />
      )}
    </div>
  );
}

/* ---------------- Create room (FR-ROOM-01) ---------------- */
function CreateRoomModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const { t } = useLang();
  const [courses, setCourses] = useState<Course[]>([]);
  const [courseId, setCourseId] = useState<number | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get<Course[]>("/courses").then((r) => {
      setCourses(r.data);
      if (r.data[0]) setCourseId(r.data[0].id);
    });
  }, []);

  const save = async () => {
    if (!name.trim() || !courseId) return;
    setBusy(true);
    setError("");
    try {
      await api.post("/rooms", {
        name: name.trim(),
        description: description.trim(),
        course_id: courseId,
      });
      onCreated();
    } catch (e: any) {
      setError(e.response?.data?.detail ?? t("rooms.createFailed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Overlay onClose={onClose}>
      <div className="flex items-center justify-between border-b border-line px-5 py-4">
        <h2 className="font-display text-lg font-bold text-ink">
          {t("rooms.createTitle")}
        </h2>
        <button
          onClick={onClose}
          className="grid h-8 w-8 place-items-center rounded-lg text-ink-faint hover:bg-surface-2 hover:text-ink"
        >
          <IconClose size={18} />
        </button>
      </div>

      <div className="flex flex-col gap-3 px-5 py-5">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={t("rooms.namePlaceholder")}
          className="rounded-xl border border-line bg-surface px-3.5 py-2.5 text-sm text-ink outline-none focus:border-accent"
        />
        <select
          value={courseId ?? ""}
          onChange={(e) => setCourseId(Number(e.target.value))}
          className="rounded-xl border border-line bg-surface px-3 py-2.5 text-sm text-ink outline-none focus:border-accent"
        >
          {courses.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder={t("rooms.descPlaceholder")}
          rows={3}
          className="resize-none rounded-xl border border-line bg-surface px-3.5 py-2.5 text-sm text-ink outline-none focus:border-accent"
        />
        {error && (
          <p className="rounded-xl bg-danger/10 px-4 py-2.5 text-sm text-danger">
            {error}
          </p>
        )}
      </div>

      <div className="border-t border-line px-5 py-4">
        <button
          onClick={save}
          disabled={!name.trim() || !courseId || busy}
          className="w-full rounded-xl bg-accent py-2.5 font-semibold text-white transition hover:brightness-105 disabled:opacity-50"
        >
          {busy ? t("docs.creating") : t("docs.create")}
        </button>
      </div>
    </Overlay>
  );
}
