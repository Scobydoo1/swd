import { useEffect, useMemo, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { api } from "../api/client";
import { useLang } from "../i18n/LanguageContext";
import { formatDateTimeVN } from "../lib/datetime";
import { MathText } from "../lib/math";
import {
  IconBook,
  IconChart,
  IconCheck,
  IconClose,
  IconSidebar,
} from "../components/Icons";
import type { AttemptReview, Course, GradeItem } from "../types";

type Ctx = { openSidebar: () => void };

function scoreTone(score: number): string {
  if (score >= 80) return "text-emerald-600 bg-emerald-500/10";
  if (score >= 50) return "text-amber-600 bg-amber-500/10";
  return "text-danger bg-danger/10";
}

export function GradePage() {
  const { openSidebar } = useOutletContext<Ctx>();
  const { t } = useLang();

  const [grades, setGrades] = useState<GradeItem[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [courseFilter, setCourseFilter] = useState<number | "all">("all");
  const [reviewing, setReviewing] = useState<AttemptReview | null>(null);

  useEffect(() => {
    api.get<GradeItem[]>("/quizzes/grades/me").then((r) => setGrades(r.data));
    api.get<Course[]>("/courses").then((r) => setCourses(r.data));
  }, []);

  const courseName = (id: number) =>
    courses.find((c) => c.id === id)?.name ?? `#${id}`;

  const filtered = useMemo(
    () =>
      courseFilter === "all"
        ? grades
        : grades.filter((g) => g.course_id === courseFilter),
    [grades, courseFilter]
  );

  // Nhóm theo môn để hiển thị mục lục bảng điểm.
  const byCourse = useMemo(() => {
    const map = new Map<number, GradeItem[]>();
    for (const g of filtered) {
      const arr = map.get(g.course_id) ?? [];
      arr.push(g);
      map.set(g.course_id, arr);
    }
    return [...map.entries()];
  }, [filtered]);

  const openReview = async (attemptId: number) => {
    const { data } = await api.get<AttemptReview>(
      `/quizzes/attempts/${attemptId}`
    );
    setReviewing(data);
  };

  return (
    <div className="h-full overflow-y-auto p-4 sm:p-8">
      <div className="mx-auto max-w-4xl">
        <header className="mb-6 flex flex-wrap items-start justify-between gap-3">
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
                {t("grade.title")}
              </h1>
            </div>
            <p className="mt-1 text-sm text-ink-faint">{t("grade.subtitle")}</p>
          </div>
          {courses.length > 0 && (
            <select
              value={courseFilter}
              onChange={(e) =>
                setCourseFilter(
                  e.target.value === "all" ? "all" : Number(e.target.value)
                )
              }
              className="rounded-xl border border-line bg-surface px-3 py-2.5 text-sm text-ink outline-none focus:border-accent"
            >
              <option value="all">{t("grade.allCourses")}</option>
              {courses.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          )}
        </header>

        {filtered.length === 0 ? (
          <div className="rounded-[20px] border border-dashed border-line bg-surface p-10 text-center text-ink-faint">
            <div className="mx-auto mb-3 grid h-14 w-14 place-items-center rounded-2xl bg-surface-2 text-accent">
              <IconChart size={26} />
            </div>
            {t("grade.empty")}
          </div>
        ) : (
          <div className="flex flex-col gap-6">
            {byCourse.map(([courseId, items]) => {
              const best = Math.max(...items.map((g) => g.score));
              return (
                <section key={courseId}>
                  <div className="mb-2 flex items-center gap-2">
                    <span className="grid h-7 w-7 place-items-center rounded-lg bg-surface-2 text-accent">
                      <IconBook size={16} />
                    </span>
                    <h2 className="font-display text-lg font-semibold text-ink">
                      {courseName(courseId)}
                    </h2>
                    <span className="ml-auto text-xs text-ink-faint">
                      {t("grade.bestScore", { score: best })}
                    </span>
                  </div>
                  <div className="overflow-hidden rounded-[18px] border border-line bg-surface shadow-maple-sm">
                    {items.map((g, idx) => (
                      <div
                        key={g.attempt_id}
                        className={`flex items-center gap-3 px-4 py-3 ${
                          idx > 0 ? "border-t border-line" : ""
                        }`}
                      >
                        <div className="min-w-0 flex-1">
                          <p className="truncate font-medium text-ink">
                            {g.quiz_title}
                          </p>
                          <p className="text-xs text-ink-faint">
                            {t("grade.takenAt")}:{" "}
                            {formatDateTimeVN(g.created_at)}
                          </p>
                        </div>
                        <span
                          className={`flex-none rounded-lg px-2.5 py-1 text-sm font-bold ${scoreTone(
                            g.score
                          )}`}
                        >
                          {g.score}%
                        </span>
                        <span className="hidden flex-none text-xs text-ink-faint sm:inline">
                          {g.correct}/{g.total}
                        </span>
                        <button
                          onClick={() => openReview(g.attempt_id)}
                          className="flex-none rounded-lg border border-line bg-surface-2 px-3 py-1.5 text-xs font-semibold text-accent transition hover:border-accent/60"
                        >
                          {t("grade.review")}
                        </button>
                      </div>
                    ))}
                  </div>
                </section>
              );
            })}
          </div>
        )}
      </div>

      {reviewing && (
        <ReviewModal review={reviewing} onClose={() => setReviewing(null)} />
      )}
    </div>
  );
}

function ReviewModal({
  review,
  onClose,
}: {
  review: AttemptReview;
  onClose: () => void;
}) {
  const { t } = useLang();
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-3"
      onClick={onClose}
    >
      <div
        className="flex max-h-[90vh] w-full max-w-xl flex-col overflow-hidden rounded-[22px] border border-line bg-bg shadow-maple"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <div className="min-w-0">
            <h2 className="truncate font-display text-lg font-bold text-ink">
              {review.quiz_title}
            </h2>
            <p className="text-xs text-ink-faint">
              {formatDateTimeVN(review.created_at)}
            </p>
          </div>
          <button
            onClick={onClose}
            className="grid h-8 w-8 flex-none place-items-center rounded-lg text-ink-faint hover:bg-surface-2 hover:text-ink"
          >
            <IconClose size={18} />
          </button>
        </div>

        <div className="mx-5 mt-5 rounded-2xl bg-accent/10 p-4 text-center">
          <div className="text-3xl font-bold text-accent">{review.score}%</div>
          <div className="text-sm text-ink-soft">
            {t("quiz.correctOf", {
              correct: review.correct,
              total: review.total,
            })}
          </div>
        </div>

        <div className="max-h-[60vh] overflow-y-auto px-5 py-5">
          {review.questions.map((q, qi) => (
            <div key={q.id} className="mb-5">
              <p className="mb-2 font-medium text-ink">
                {qi + 1}. <MathText>{q.text}</MathText>
              </p>
              <div className="flex flex-col gap-2">
                {q.options.map((opt, oi) => {
                  const picked = q.your_index === oi;
                  let tone = "border-line bg-surface";
                  if (oi === q.correct_index)
                    tone = "border-emerald-500/60 bg-emerald-500/10";
                  else if (picked && !q.is_correct)
                    tone = "border-danger/60 bg-danger/10";
                  return (
                    <div
                      key={oi}
                      className={`flex items-center gap-3 rounded-xl border px-3.5 py-2.5 text-sm ${tone}`}
                    >
                      <span
                        className={`grid h-5 w-5 flex-none place-items-center rounded-full border text-[11px] ${
                          picked
                            ? "border-accent text-accent"
                            : "border-ink-faint text-ink-faint"
                        }`}
                      >
                        {String.fromCharCode(65 + oi)}
                      </span>
                      <span className="text-ink">
                        <MathText>{opt}</MathText>
                      </span>
                      {oi === q.correct_index && (
                        <span className="ml-auto text-emerald-600">
                          <IconCheck size={16} />
                        </span>
                      )}
                      {picked && (
                        <span className="ml-1 flex-none rounded bg-surface-2 px-1.5 py-0.5 text-[10px] text-ink-faint">
                          {t("grade.yourAnswer")}
                        </span>
                      )}
                    </div>
                  );
                })}
                {q.your_index === null && (
                  <p className="text-xs text-ink-faint">
                    {t("grade.notAnswered")}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="border-t border-line px-5 py-4">
          <button
            onClick={onClose}
            className="w-full rounded-xl bg-accent py-2.5 font-semibold text-white transition hover:brightness-105"
          >
            {t("grade.close")}
          </button>
        </div>
      </div>
    </div>
  );
}
