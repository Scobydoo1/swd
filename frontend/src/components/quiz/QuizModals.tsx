import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { useLang } from "../../i18n/LanguageContext";
import { formatDateTimeVN } from "../../lib/datetime";
import { MathText } from "../../lib/math";
import type { AttemptResult, QuizAttemptRow, QuizDetail } from "../../types";
import { IconCheck, IconClose } from "../Icons";

export function Overlay({
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

/* ---------------- Take quiz (FR-QZ-02/03) ---------------- */
export function TakeQuizModal({
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
                {qi + 1}. <MathText>{q.text}</MathText>
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
                      <span className="text-ink"><MathText>{opt}</MathText></span>
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

/* ---------------- Attempts board (FR-QZ-04: Lecturer xem điểm SV) ------- */
export function AttemptsModal({
  quizId,
  quizTitle,
  onClose,
}: {
  quizId: number;
  quizTitle: string;
  onClose: () => void;
}) {
  const { t } = useLang();
  const [attempts, setAttempts] = useState<QuizAttemptRow[] | null>(null);

  useEffect(() => {
    api
      .get<QuizAttemptRow[]>(`/quizzes/${quizId}/attempts`)
      .then((r) => setAttempts(r.data))
      .catch(() => setAttempts([]));
  }, [quizId]);

  return (
    <Overlay onClose={onClose}>
      <div className="flex items-center justify-between border-b border-line px-5 py-4">
        <h2 className="font-display text-lg font-bold text-ink">
          {t("quiz.resultsTitle", { title: quizTitle })}
        </h2>
        <button
          onClick={onClose}
          className="grid h-8 w-8 place-items-center rounded-lg text-ink-faint hover:bg-surface-2 hover:text-ink"
        >
          <IconClose size={18} />
        </button>
      </div>

      <div className="max-h-[60vh] overflow-y-auto px-5 py-5">
        {attempts === null ? (
          <p className="text-sm text-ink-faint">…</p>
        ) : attempts.length === 0 ? (
          <p className="rounded-xl border border-dashed border-line bg-surface p-6 text-center text-sm text-ink-faint">
            {t("quiz.noAttempts")}
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wider text-ink-faint">
                <th className="pb-2 font-semibold">{t("quiz.colStudent")}</th>
                <th className="pb-2 font-semibold">{t("quiz.colScore")}</th>
                <th className="pb-2 font-semibold">{t("quiz.colTime")}</th>
              </tr>
            </thead>
            <tbody>
              {attempts.map((a) => (
                <tr key={a.id} className="border-t border-line-soft">
                  <td className="py-2.5">
                    <div className="font-medium text-ink">
                      {a.user_name ?? t("quiz.deletedUser")}
                    </div>
                    {a.user_email && (
                      <div className="text-xs text-ink-faint">{a.user_email}</div>
                    )}
                  </td>
                  <td className="py-2.5">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-bold ${
                        a.score >= 50
                          ? "bg-emerald-500/10 text-emerald-600"
                          : "bg-danger/10 text-danger"
                      }`}
                    >
                      {a.score}%
                    </span>
                  </td>
                  <td className="py-2.5 text-ink-faint">
                    {formatDateTimeVN(a.created_at)}
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
