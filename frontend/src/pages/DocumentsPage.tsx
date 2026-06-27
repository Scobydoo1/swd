import { useEffect, useRef, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { useLang } from "../i18n/LanguageContext";
import { IconSidebar, IconTrash, IconUpload } from "../components/Icons";
import type { Course, Document } from "../types";

const statusStyle: Record<string, string> = {
  INDEXED: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
  PROCESSING: "bg-amber-500/15 text-amber-600 dark:text-amber-400",
  FAILED: "bg-danger/15 text-danger",
};
const typeIcon: Record<string, string> = {
  PDF: "📄",
  DOCX: "📝",
  PPTX: "📊",
};

export function DocumentsPage() {
  const { user } = useAuth();
  const { t } = useLang();
  const { openSidebar } = useOutletContext<{ openSidebar: () => void }>();
  const canManage = user?.role === "ADMIN" || user?.role === "LECTURER";

  const [docs, setDocs] = useState<Document[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [courseId, setCourseId] = useState<number | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  // Tạo môn học mới
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [creating, setCreating] = useState(false);

  // Chỉ tải tài liệu của môn đang chọn — tạo môn mới sẽ KHÔNG còn thấy tài
  // liệu của môn cũ (mỗi môn có kho tài liệu riêng).
  const load = (cid: number | null = courseId) => {
    if (!cid) {
      setDocs([]);
      return Promise.resolve();
    }
    return api
      .get<Document[]>("/documents", { params: { course_id: cid } })
      .then((r) => setDocs(r.data));
  };

  const loadCourses = (selectId?: number) =>
    api.get<Course[]>("/courses").then((r) => {
      setCourses(r.data);
      const pick = selectId ?? courseId ?? r.data[0]?.id ?? null;
      setCourseId(pick);
    });

  useEffect(() => {
    loadCourses();
  }, []);

  // Đổi môn (kể cả vừa tạo môn mới) -> tải lại tài liệu đúng môn đó.
  useEffect(() => {
    load(courseId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [courseId]);

  const createCourse = async () => {
    if (!newName.trim()) return;
    setError("");
    setCreating(true);
    try {
      const { data } = await api.post<Course>("/courses", {
        name: newName.trim(),
        description: newDesc.trim(),
      });
      await loadCourses(data.id);
      setShowCreate(false);
      setNewName("");
      setNewDesc("");
    } catch (e: any) {
      setError(e.response?.data?.detail ?? t("docs.createFailed"));
    } finally {
      setCreating(false);
    }
  };

  const upload = async (file: File) => {
    if (!courseId) return;
    setError("");
    setUploading(true);
    const form = new FormData();
    form.append("file", file);
    form.append("course_id", String(courseId));
    try {
      await api.post("/documents", form);
      await load();
    } catch (e: any) {
      setError(e.response?.data?.detail ?? t("docs.uploadFailed"));
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const remove = async (id: number) => {
    if (!confirm(t("docs.removeConfirm"))) return;
    await api.delete(`/documents/${id}`);
    load();
  };

  const removeCourse = async () => {
    const course = courses.find((c) => c.id === courseId);
    if (!course) return;
    if (!confirm(t("docs.deleteCourseConfirm", { name: course.name }))) return;
    setError("");
    try {
      await api.delete(`/courses/${course.id}`);
      setCourseId(null);
      await loadCourses();
      await load();
    } catch (e: any) {
      setError(e.response?.data?.detail ?? t("docs.deleteCourseFailed"));
    }
  };

  return (
    <div className="h-full overflow-y-auto p-4 sm:p-8">
      <div className="mx-auto max-w-5xl">
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
              {t("docs.title")}
            </h1>
          </div>
          <p className="mt-1 text-sm text-ink-faint">{t("docs.subtitle")}</p>
        </header>

        <div className="mb-6 flex flex-wrap items-center gap-3">
          <label className="text-sm font-medium text-ink-soft">{t("docs.course")}</label>
          <select
            value={courseId ?? ""}
            onChange={(e) => setCourseId(Number(e.target.value))}
            className="rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink outline-none focus:border-accent"
          >
            {courses.length === 0 && <option value="">{t("docs.noCourse")}</option>}
            {courses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          {canManage && (
            <button
              onClick={() => setShowCreate((v) => !v)}
              className="rounded-xl border border-line bg-surface px-3 py-2 text-sm font-medium text-accent transition hover:border-accent/60 hover:bg-surface-2"
            >
              {showCreate ? t("common.cancel") : t("docs.createCourse")}
            </button>
          )}
          {canManage && courseId && (
            <button
              onClick={removeCourse}
              title={t("docs.deleteCourse")}
              className="flex items-center gap-1.5 rounded-xl border border-line bg-surface px-3 py-2 text-sm font-medium text-ink-faint transition hover:border-danger/50 hover:bg-danger/10 hover:text-danger"
            >
              <IconTrash size={15} /> {t("docs.deleteCourse")}
            </button>
          )}
        </div>

        {canManage && showCreate && (
          <div className="mb-6 rounded-[20px] border border-line bg-surface p-5">
            <h2 className="mb-3 text-sm font-semibold text-ink">
              {t("docs.createCourseTitle")}
            </h2>
            <div className="flex flex-col gap-3 sm:flex-row">
              <input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder={t("docs.courseName")}
                className="flex-1 rounded-xl border border-line bg-surface-2 px-3 py-2 text-sm text-ink outline-none focus:border-accent"
              />
              <input
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                placeholder={t("docs.descriptionOptional")}
                className="flex-1 rounded-xl border border-line bg-surface-2 px-3 py-2 text-sm text-ink outline-none focus:border-accent"
              />
              <button
                onClick={createCourse}
                disabled={creating || !newName.trim()}
                className="rounded-xl bg-accent px-4 py-2 text-sm font-semibold text-white transition hover:bg-accent/90 disabled:opacity-50"
              >
                {creating ? t("docs.creating") : t("docs.create")}
              </button>
            </div>
          </div>
        )}

        {/* Upload zone */}
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            if (e.dataTransfer.files[0]) upload(e.dataTransfer.files[0]);
          }}
          onClick={() => fileRef.current?.click()}
          className="mb-8 cursor-pointer rounded-[24px] border-2 border-dashed border-line bg-surface p-6 text-center transition hover:border-accent/60 hover:bg-surface-2 sm:p-10"
        >
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.docx,.pptx"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])}
          />
          {uploading ? (
            <div className="text-accent">
              <div className="mx-auto mb-3 h-8 w-8 animate-spin rounded-full border-4 border-line border-t-accent" />
              {t("docs.processing")}
            </div>
          ) : (
            <>
              <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-surface-2 text-accent">
                <IconUpload size={26} />
              </div>
              <p className="mt-3 font-semibold text-ink">{t("docs.dropOrClick")}</p>
              <p className="mt-1 text-xs text-ink-faint">{t("docs.supports")}</p>
            </>
          )}
        </div>

        {error && (
          <p className="mb-4 rounded-xl bg-danger/10 px-4 py-2.5 text-sm text-danger">
            {error}
          </p>
        )}

        {/* Document list */}
        <div className="overflow-hidden rounded-[20px] border border-line bg-surface">
          <div className="grid grid-cols-12 gap-3 border-b border-line bg-surface-2 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-ink-faint sm:px-5">
            <div className="col-span-7 sm:col-span-6">{t("docs.colDoc")}</div>
            <div className="hidden sm:col-span-2 sm:block">{t("docs.colChunks")}</div>
            <div className="col-span-3 sm:col-span-2">{t("docs.colStatus")}</div>
            <div className="col-span-2 text-right">{t("docs.colActions")}</div>
          </div>
          {docs.length === 0 && (
            <p className="px-5 py-10 text-center text-sm text-ink-faint">
              {t("docs.empty")}
            </p>
          )}
          {docs.map((d) => (
            <div
              key={d.id}
              className="grid grid-cols-12 items-center gap-3 border-b border-line-soft px-4 py-3.5 text-sm transition last:border-0 hover:bg-surface-2/50 sm:px-5"
            >
              <div className="col-span-7 flex min-w-0 items-center gap-3 sm:col-span-6">
                <span className="text-xl">{typeIcon[d.file_type]}</span>
                <span className="truncate font-medium text-ink">
                  {d.filename}
                </span>
              </div>
              <div className="hidden text-ink-soft sm:col-span-2 sm:block">{d.num_chunks}</div>
              <div className="col-span-3 sm:col-span-2">
                <span
                  className={`rounded-full px-2.5 py-1 text-xs font-medium ${statusStyle[d.status]}`}
                >
                  {t(`docs.status${d.status}`)}
                </span>
              </div>
              <div className="col-span-2 flex justify-end">
                <button
                  onClick={() => remove(d.id)}
                  className="grid h-8 w-8 place-items-center rounded-lg text-ink-faint transition hover:bg-danger/10 hover:text-danger"
                  title={t("common.delete")}
                >
                  <IconTrash size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
