import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { useLang } from "../i18n/LanguageContext";
import {
  IconChart,
  IconCheck,
  IconClose,
  IconPlus,
  IconQuiz,
  IconSidebar,
  IconSpark,
  IconTrash,
} from "../components/Icons";
import {
  AttemptsModal,
  Overlay,
  TakeQuizModal,
} from "../components/quiz/QuizModals";
import type {
  Course,
  GeneratedQuiz,
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
  const [viewingResults, setViewingResults] = useState<QuizListItem | null>(
    null
  );

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
                <div className="mt-4 flex gap-2">
                  <button
                    onClick={() => openTake(q.id)}
                    className="flex-1 rounded-xl border border-line bg-surface-2 py-2 text-sm font-semibold text-accent transition hover:border-accent/60"
                  >
                    {canManage ? t("quiz.viewTry") : t("quiz.take")}
                  </button>
                  {canManage && (
                    <button
                      onClick={() => setViewingResults(q)}
                      className="flex items-center gap-1.5 rounded-xl border border-line bg-surface-2 px-3 py-2 text-sm font-semibold text-ink-soft transition hover:border-accent/60 hover:text-accent"
                      title={t("quiz.results")}
                    >
                      <IconChart size={16} /> {t("quiz.results")}
                    </button>
                  )}
                </div>
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
      {viewingResults && (
        <AttemptsModal
          quizId={viewingResults.id}
          quizTitle={viewingResults.title}
          onClose={() => setViewingResults(null)}
        />
      )}
    </div>
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

  // FR-QZ-05: AI soạn nháp đề để Lecturer duyệt/sửa.
  const [aiTopic, setAiTopic] = useState("");
  const [aiNum, setAiNum] = useState(5);
  const [aiBusy, setAiBusy] = useState(false);
  const [aiInfo, setAiInfo] = useState("");

  useEffect(() => {
    api.get<Course[]>("/courses").then((r) => {
      setCourses(r.data);
      if (r.data[0]) setCourseId(r.data[0].id);
    });
  }, []);

  const patchQ = (i: number, patch: Partial<DraftQuestion>) =>
    setQuestions((qs) => qs.map((q, j) => (j === i ? { ...q, ...patch } : q)));

  const generateAi = async () => {
    if (!courseId) {
      setError(t("quiz.aiNeedCourse"));
      return;
    }
    setAiBusy(true);
    setError("");
    setAiInfo("");
    try {
      const { data } = await api.post<GeneratedQuiz>("/quizzes/generate", {
        course_id: courseId,
        num_questions: Math.min(50, Math.max(1, Math.floor(aiNum) || 1)),
        topic: aiTopic.trim() || null,
      });
      // Đổ nháp AID vào form để Lecturer chỉnh sửa (pad đủ 4 lựa chọn).
      setQuestions(
        data.questions.map((q) => {
          const options = [...q.options];
          while (options.length < 4) options.push("");
          return {
            text: q.text,
            options,
            correct_index: q.correct_index,
          };
        })
      );
      if (!title.trim()) setTitle(data.title);
      setAiInfo(t("quiz.aiReview"));
    } catch (e: any) {
      setError(e.response?.data?.detail ?? t("quiz.aiFailed"));
    } finally {
      setAiBusy(false);
    }
  };

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

        {/* FR-QZ-05: Khu vực AI soạn nháp đề để Lecturer duyệt/sửa */}
        <div className="mb-4 rounded-2xl border border-accent/30 bg-accent/5 p-4">
          <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-accent">
            <IconSpark size={16} /> {t("quiz.aiTitle")}
          </div>
          <p className="mb-3 text-xs text-ink-faint">{t("quiz.aiHint")}</p>
          <div className="flex flex-col gap-2 sm:flex-row">
            <input
              value={aiTopic}
              onChange={(e) => setAiTopic(e.target.value)}
              placeholder={t("quiz.aiTopicPlaceholder")}
              className="flex-1 rounded-xl border border-line bg-surface px-3.5 py-2 text-sm text-ink outline-none focus:border-accent"
            />
            <input
              type="number"
              min={1}
              max={50}
              value={aiNum}
              onChange={(e) => setAiNum(Number(e.target.value))}
              title={t("quiz.aiNumQuestions")}
              placeholder={t("quiz.aiNumQuestions")}
              className="w-full rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink outline-none focus:border-accent sm:w-28"
            />
            <button
              type="button"
              onClick={generateAi}
              disabled={aiBusy}
              className="flex items-center justify-center gap-1.5 rounded-xl bg-accent px-4 py-2 text-sm font-semibold text-white transition hover:brightness-105 disabled:opacity-50"
            >
              <IconSpark size={15} />
              {aiBusy ? t("quiz.aiGenerating") : t("quiz.aiGenerateBtn")}
            </button>
          </div>
          {aiInfo && (
            <p className="mt-2.5 rounded-lg bg-emerald-500/10 px-3 py-2 text-xs text-emerald-700">
              {aiInfo}
            </p>
          )}
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
