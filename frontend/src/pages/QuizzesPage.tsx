import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { useLang } from "../i18n/LanguageContext";
import {
  IconCheck,
  IconClose,
  IconPlus,
  IconQuiz,
  IconSidebar,
  IconTrash,
} from "../components/Icons";
import type {
  AttemptResult,
  Course,
  QuizDetail,
  QuizListItem,
} from "../types";

type Ctx = { openSidebar: () => void };

interface DraftQuestion {
  text: string;
  options: string[];
  correct_index: number;
}

const emptyQuestion = (): DraftQuestion => ({
  text: "",
  options: ["", "", "", ""],
  correct_index: 0,
});

export function QuizzesPage() {
  const { openSidebar } = useOutletContext<Ctx>();
  const { user } = useAuth();
  const { t } = useLang();
  const canManage = user?.role === "ADMIN" || user?.role === "LECTURER";

  const [quizzes, setQuizzes] = useState<QuizListItem[]>([]);
  const [creating, setCreating] = useState(false);
  const [taking, setTaking] = useState<QuizDetail | null>(null);

  const load = () =>
    api.get<QuizListItem[]>("/quizzes").then((r) => setQuizzes(r.data));
  useEffect(() => {
    load();
  }, []);

  const remove = async (id: number) => {
    if (!confirm(t("quiz.deleteConfirm"))) return;
    await api.delete(`/quizzes/${id}`);
    load();
  };

  const openTake = async (id: number) => {
    const { data } = await api.get<QuizDetail>(`/quizzes/${id}`);
    setTaking(data);
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
              <h1 className="font-display text-2xl font-bold text-ink">{t("nav.quiz")}</h1>
            </div>
            <p className="mt-1 text-sm text-ink-faint">
              {canManage ? t("quiz.subtitleManage") : t("quiz.subtitleTake")}
            </p>
          </div>
          {canManage && (
            <button
              onClick={() => setCreating(true)}
              className="flex flex-none items-center gap-2 rounded-xl bg-accent px-3.5 py-2.5 text-sm font-semibold text-white shadow-maple-sm transition hover:brightness-105"
            >
              <IconPlus size={17} /> {t("quiz.create")}
            </button>
          )}
        </header>

        {quizzes.length === 0 ? (
          <div className="rounded-[20px] border border-dashed border-line bg-surface p-10 text-center text-ink-faint">
            <div className="mx-auto mb-3 grid h-14 w-14 place-items-center rounded-2xl bg-surface-2 text-accent">
              <IconQuiz size={26} />
            </div>
            {t("quiz.empty")}
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {quizzes.map((q) => (
              <div
                key={q.id}
                className="flex flex-col rounded-[18px] border border-line bg-surface p-5 shadow-maple-sm transition hover:border-accent/40"
              >
                <div className="flex items-start gap-3">
                  <span className="grid h-10 w-10 flex-none place-items-center rounded-xl bg-surface-2 text-accent">
                    <IconQuiz size={20} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <h3 className="truncate font-semibold text-ink">{q.title}</h3>
                    <p className="text-xs text-ink-faint">
                      {t("quiz.numQuestions", { n: q.num_questions })}
                    </p>
                  </div>
                  {canManage && (
                    <button
                      onClick={() => remove(q.id)}
                      className="grid h-8 w-8 flex-none place-items-center rounded-lg text-ink-faint transition hover:bg-danger/10 hover:text-danger"
                      title={t("common.delete")}
                    >
                      <IconTrash size={16} />
                    </button>
                  )}
                </div>
                <button
                  onClick={() => openTake(q.id)}
                  className="mt-4 rounded-xl border border-line bg-surface-2 py-2 text-sm font-semibold text-accent transition hover:border-accent/60"
                >
                  {canManage ? t("quiz.viewTry") : t("quiz.take")}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {creating && (
        <CreateQuizModal
          onClose={() => setCreating(false)}
          onCreated={() => {
            setCreating(false);
            load();
          }}
        />
      )}
      {taking && (
        <TakeQuizModal quiz={taking} onClose={() => setTaking(null)} />
      )}
    </div>
  );
}

/* ---------------- Take quiz ---------------- */
function TakeQuizModal({
  quiz,
  onClose,
}: {
  quiz: QuizDetail;
  onClose: () => void;
}) {
  const { t } = useLang();
  const [answers, setAnswers] = useState<(number | null)[]>(
    quiz.questions.map(() => null)
  );
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setBusy(true);
    try {
      const { data } = await api.post<AttemptResult>(
        `/quizzes/${quiz.id}/submit`,
        { answers: answers.map((a) => (a === null ? -1 : a)) }
      );
      setResult(data);
    } finally {
      setBusy(false);
    }
  };

  const resultFor = (qi: number) =>
    result?.results.find((r) => r.question_id === quiz.questions[qi].id);

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

      {result && (
        <div className="mx-5 mt-5 rounded-2xl bg-accent/10 p-4 text-center">
          <div className="text-3xl font-bold text-accent">{result.score}%</div>
          <div className="text-sm text-ink-soft">
            {t("quiz.correctOf", { correct: result.correct, total: result.total })}
          </div>
        </div>
      )}

      <div className="max-h-[60vh] overflow-y-auto px-5 py-5">
        {quiz.questions.map((q, qi) => {
          const r = resultFor(qi);
          return (
            <div key={q.id} className="mb-5">
              <p className="mb-2 font-medium text-ink">
                {qi + 1}. {q.text}
              </p>
              <div className="flex flex-col gap-2">
                {q.options.map((opt, oi) => {
                  const picked = answers[qi] === oi;
                  let tone =
                    "border-line bg-surface hover:border-accent/50";
                  if (result && r) {
                    if (oi === r.correct_index)
                      tone = "border-emerald-500/60 bg-emerald-500/10";
                    else if (picked && !r.is_correct)
                      tone = "border-danger/60 bg-danger/10";
                  } else if (picked) {
                    tone = "border-accent bg-accent/10";
                  }
                  return (
                    <button
                      key={oi}
                      disabled={!!result}
                      onClick={() =>
                        setAnswers((a) =>
                          a.map((v, i) => (i === qi ? oi : v))
                        )
                      }
                      className={`flex items-center gap-3 rounded-xl border px-3.5 py-2.5 text-left text-sm transition ${tone}`}
                    >
                      <span
                        className={`grid h-5 w-5 flex-none place-items-center rounded-full border text-[11px] ${
                          picked ? "border-accent text-accent" : "border-ink-faint text-ink-faint"
                        }`}
                      >
                        {String.fromCharCode(65 + oi)}
                      </span>
                      <span className="text-ink">{opt}</span>
                      {result && r && oi === r.correct_index && (
                        <span className="ml-auto text-emerald-600">
                          <IconCheck size={16} />
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      <div className="border-t border-line px-5 py-4">
        {result ? (
          <button
            onClick={onClose}
            className="w-full rounded-xl bg-accent py-2.5 font-semibold text-white transition hover:brightness-105"
          >
            {t("quiz.finish")}
          </button>
        ) : (
          <button
            onClick={submit}
            disabled={busy || answers.some((a) => a === null)}
            className="w-full rounded-xl bg-accent py-2.5 font-semibold text-white transition hover:brightness-105 disabled:opacity-50"
          >
            {busy ? t("quiz.grading") : t("quiz.submit")}
          </button>
        )}
      </div>
    </Overlay>
  );
}

/* ---------------- Create quiz ---------------- */
function CreateQuizModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const { t } = useLang();
  const [courses, setCourses] = useState<Course[]>([]);
  const [courseId, setCourseId] = useState<number | null>(null);
  const [title, setTitle] = useState("");
  const [questions, setQuestions] = useState<DraftQuestion[]>([
    emptyQuestion(),
  ]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get<Course[]>("/courses").then((r) => {
      setCourses(r.data);
      if (r.data[0]) setCourseId(r.data[0].id);
    });
  }, []);

  const patchQ = (i: number, patch: Partial<DraftQuestion>) =>
    setQuestions((qs) => qs.map((q, j) => (j === i ? { ...q, ...patch } : q)));

  const valid =
    !!courseId &&
    title.trim() &&
    questions.every(
      (q) =>
        q.text.trim() &&
        q.options.filter((o) => o.trim()).length >= 2 &&
        q.options[q.correct_index]?.trim()
    );

  const save = async () => {
    if (!valid || !courseId) return;
    setBusy(true);
    setError("");
    try {
      await api.post("/quizzes", {
        course_id: courseId,
        title: title.trim(),
        questions: questions.map((q) => {
          const options = q.options.filter((o) => o.trim());
          return {
            text: q.text.trim(),
            options,
            correct_index: Math.min(q.correct_index, options.length - 1),
          };
        }),
      });
      onCreated();
    } catch (e: any) {
      setError(e.response?.data?.detail ?? t("quiz.createFailed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Overlay onClose={onClose}>
      <div className="flex items-center justify-between border-b border-line px-5 py-4">
        <h2 className="font-display text-lg font-bold text-ink">{t("quiz.createTitle")}</h2>
        <button
          onClick={onClose}
          className="grid h-8 w-8 place-items-center rounded-lg text-ink-faint hover:bg-surface-2 hover:text-ink"
        >
          <IconClose size={18} />
        </button>
      </div>

      <div className="max-h-[64vh] overflow-y-auto px-5 py-5">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder={t("quiz.titlePlaceholder")}
            className="flex-1 rounded-xl border border-line bg-surface px-3.5 py-2.5 text-sm text-ink outline-none focus:border-accent"
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
        </div>

        {questions.map((q, qi) => (
          <div
            key={qi}
            className="mb-4 rounded-2xl border border-line bg-surface-2/40 p-4"
          >
            <div className="mb-2 flex items-center gap-2">
              <span className="text-sm font-semibold text-ink-soft">
                {t("quiz.questionN", { n: qi + 1 })}
              </span>
              {questions.length > 1 && (
                <button
                  onClick={() =>
                    setQuestions((qs) => qs.filter((_, j) => j !== qi))
                  }
                  className="ml-auto grid h-7 w-7 place-items-center rounded-lg text-ink-faint hover:bg-danger/10 hover:text-danger"
                  title={t("quiz.deleteQuestion")}
                >
                  <IconTrash size={15} />
                </button>
              )}
            </div>
            <input
              value={q.text}
              onChange={(e) => patchQ(qi, { text: e.target.value })}
              placeholder={t("quiz.questionContent")}
              className="mb-3 w-full rounded-xl border border-line bg-surface px-3.5 py-2 text-sm text-ink outline-none focus:border-accent"
            />
            <p className="mb-1.5 text-xs text-ink-faint">{t("quiz.markCorrect")}</p>
            <div className="flex flex-col gap-2">
              {q.options.map((opt, oi) => (
                <div key={oi} className="flex items-center gap-2">
                  <button
                    onClick={() => patchQ(qi, { correct_index: oi })}
                    title={t("quiz.correctAnswer")}
                    className={`grid h-6 w-6 flex-none place-items-center rounded-full border text-[11px] ${
                      q.correct_index === oi
                        ? "border-emerald-500 bg-emerald-500/15 text-emerald-600"
                        : "border-ink-faint text-ink-faint"
                    }`}
                  >
                    {q.correct_index === oi ? <IconCheck size={13} /> : String.fromCharCode(65 + oi)}
                  </button>
                  <input
                    value={opt}
                    onChange={(e) =>
                      patchQ(qi, {
                        options: q.options.map((o, j) =>
                          j === oi ? e.target.value : o
                        ),
                      })
                    }
                    placeholder={t("quiz.optionN", { n: oi + 1 })}
                    className="flex-1 rounded-lg border border-line bg-surface px-3 py-1.5 text-sm text-ink outline-none focus:border-accent"
                  />
                </div>
              ))}
            </div>
          </div>
        ))}

        <button
          onClick={() => setQuestions((qs) => [...qs, emptyQuestion()])}
          className="flex items-center gap-2 rounded-xl border border-dashed border-line px-3.5 py-2 text-sm font-medium text-accent transition hover:border-accent/60 hover:bg-surface-2"
        >
          <IconPlus size={16} /> {t("quiz.addQuestion")}
        </button>

        {error && (
          <p className="mt-3 rounded-xl bg-danger/10 px-4 py-2.5 text-sm text-danger">
            {error}
          </p>
        )}
      </div>

      <div className="border-t border-line px-5 py-4">
        <button
          onClick={save}
          disabled={!valid || busy}
          className="w-full rounded-xl bg-accent py-2.5 font-semibold text-white transition hover:brightness-105 disabled:opacity-50"
        >
          {busy ? t("quiz.saving") : t("quiz.save")}
        </button>
      </div>
    </Overlay>
  );
}

function Overlay({
  children,
  onClose,
}: {
  children: React.ReactNode;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-3"
      onClick={onClose}
    >
      <div
        className="flex max-h-[90vh] w-full max-w-xl flex-col overflow-hidden rounded-[22px] border border-line bg-bg shadow-maple"
        onClick={(e) => e.stopPropagation()}
      >
        {children}
      </div>
    </div>
  );
}
