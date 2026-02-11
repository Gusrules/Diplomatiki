import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../lib/api.js";
import Toast from "../components/Toast.jsx";
import InfoBox from "../components/InfoBox.jsx";
import { getUserId } from "../lib/session.js";

export default function AdaptiveQuizPage() {
  const FIXED_N = 10;
  const { moduleId } = useParams();

  const userId = getUserId();
  const [quizId, setQuizId] = useState(null);

  const [qs, setQs] = useState([]);
  const [answers, setAnswers] = useState({});
  const [err, setErr] = useState("");
  const [result, setResult] = useState(null);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const answeredCount = qs.filter((q) => answers[q.id] !== undefined).length;
  const allAnswered = qs.length > 0 && answeredCount === qs.length;


  async function load() {
    try {
      setErr("");
      setIsLoading(true);

      const mod = await api.getModule(moduleId);
      const subjectId = mod.subject_id;

      const sess = await api.getAdaptiveQuizSession({
        userId,
        subjectId,
        moduleId: Number(moduleId),
        n: FIXED_N,
      });

      setQuizId(sess.quiz_id ?? null);
      setQs(Array.isArray(sess.questions) ? sess.questions : []);
      setAnswers({});
      setResult(null);
    } catch (e) {
      setErr(e.message);
      setQuizId(null);
      setQs([]);
      setAnswers({});
      setResult(null);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [moduleId]);

  async function submit() {
    if (!qs.length) return setErr("No questions loaded.");
    if (!quizId) return setErr("Quiz id not loaded yet.");

    const missing = qs.filter((q) => answers[q.id] === undefined);
    if (missing.length > 0) {
      return setErr("Please select an option (A/B/C/D) for every question before submitting.");
    }

    const payload = {
      user_id: Number(userId),
      quiz_id: Number(quizId),
      answers: qs.map((q) => ({
        question_id: q.id,
        selected_index: Number(answers[q.id]),
      })),
    };

    try {
      setIsSubmitting(true);
      setErr("");
      const out = await api.submitAttemptAnswers(payload);
      setResult(out);
    } catch (e) {
      setErr(e.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <button
        className="btn"
        onClick={() => window.history.back()}
        style={{ justifySelf: "start" }}
      >
        ← Back to module
      </button>

      <div>
        <h2 style={{ margin: 0 }}>Adaptive Quiz</h2>
        <div style={{ color: "rgba(255,255,255,.7)", marginTop: 6 }}>
          Module #{moduleId} • {FIXED_N} questions
        </div>
      </div>

      <InfoBox title="Adaptive quiz">
        <div>Questions are selected based on your current skill level and difficulty_score.</div>
        <div>Submitting updates difficulty + user level, affecting the next selection.</div>
      </InfoBox>

      {result && (
        <div className="card">
          <div style={{ fontWeight: 900, marginBottom: 6 }}>Result</div>
          <div>Score: {result.score}%</div>
          <div>
            Correct: {result.correct_answers}/{result.total_questions}
          </div>

          <div style={{ marginTop: 10 }}>
            <button className="btn btn-primary" onClick={load} disabled={isLoading}>
              {isLoading ? "Loading..." : "Next questions"}
            </button>
          </div>
        </div>
      )}

      {qs.length === 0 ? (
        <div className="card" style={{ color: "rgba(255,255,255,.75)" }}>
          {isLoading ? "Loading questions…" : "No questions loaded yet."}
        </div>
      ) : (
        <div style={{ display: "grid", gap: 10 }}>
          {qs.map((q, qIndex) => (
            <div key={q.id} className="card">
              <div style={{ fontWeight: 900, marginBottom: 8 }}>{qIndex + 1}. {q.prompt}</div>

              <div style={{ display: "grid", gap: 8 }}>
                {(q.choices || []).map((c, idx) => (
                  <label
                    key={idx}
                    style={{
                      display: "flex",
                      gap: 10,
                      alignItems: "flex-start",
                      padding: "6px 0",
                      cursor: "pointer",
                    }}
                  >
                    <input
                      type="radio"
                      name={`q-${q.id}`}
                      checked={answers[q.id] === idx}
                      onChange={() => setAnswers((a) => ({ ...a, [q.id]: idx }))}
                    />
                    <span style={{ fontWeight: 900 }}>{String.fromCharCode(65 + idx)}.</span>
                    <span style={{ flex: 1, whiteSpace: "pre-wrap" }}>{c}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Bottom actions (sticky) */}
      {!result && qs.length > 0 && (
        <div
          className="card"
          style={{
            position: "sticky",
            bottom: 12,
            zIndex: 10,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: 12,
            padding: 12,
          }}
        >
          <div style={{ color: "rgba(255,255,255,.7)", fontSize: 13 }}>
            Answered: <b>{answeredCount}</b> / {qs.length}
          </div>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button className="btn" onClick={load} disabled={isLoading}>
              {isLoading ? "Loading..." : "Reload"}
            </button>

            <button
              className="btn btn-primary"
              onClick={() => {
                if (!allAnswered) {
                  setErr("Please answer all questions before submitting.");
                  return;
                }
                submit();
              }}
              disabled={!quizId || isSubmitting}
            >
              {isSubmitting ? "Submitting..." : "Submit"}
            </button>
          </div>
        </div>
      )}


      <Toast message={err} onClose={() => setErr("")} />
    </div>
  );
}
