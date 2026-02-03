import React, { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api.js";
import { getUserId } from "../lib/session.js";
import Toast from "../components/Toast.jsx";

export default function SubjectQuizPage() {
  const { subjectId } = useParams();
  const userId = getUserId();

  const [subject, setSubject] = useState(null);
  const [quizId, setQuizId] = useState(null);
  const [qs, setQs] = useState([]);
  const [answers, setAnswers] = useState({}); // { [questionId]: selected_index }
  const [result, setResult] = useState(null);
  const [err, setErr] = useState("");

  const total = qs.length;

  const answeredCount = useMemo(() => {
    let c = 0;
    for (const q of qs) {
      if (answers[q.id] !== undefined) c += 1;
    }
    return c;
  }, [qs, answers]);

  async function start() {
    try {
      setErr("");
      setResult(null);
      setAnswers({});
      setQuizId(null);

      const s = await api.getSubjectFromList(subjectId);
      setSubject(s);

      // ✅ απαιτείται να υπάρχει το endpoint /adaptive-quiz/session
      const sess = await api.getAdaptiveQuizSession({
        userId,
        subjectId: Number(subjectId),
        moduleId: null,
        n: 10,
      });

      setQuizId(sess.quiz_id);
      setQs(Array.isArray(sess.questions) ? sess.questions : []);
    } catch (e) {
      setErr(e.message);
    }
  }

  async function submit() {
    try {
      setErr("");
      if (!quizId) throw new Error("No quiz session id");
      if (qs.length === 0) throw new Error("No questions");

      const payload = {
        user_id: userId,
        quiz_id: quizId,
        answers: qs.map((q) => ({
          question_id: q.id,
          selected_index: answers[q.id] ?? -1,
          response_time: 0,
        })),
      };

      // backend expects selected_index 0..3, so block submit if incomplete
      if (payload.answers.some((a) => a.selected_index < 0)) {
        throw new Error("Answer all questions first.");
      }

      const out = await api.submitAttemptAnswers(payload);
      setResult(out);
    } catch (e) {
      setErr(e.message);
    }
  }

  useEffect(() => {
    start();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [subjectId]);

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div>
        <h2 style={{ marginBottom: 6 }}>{subject?.name || "Subject quiz"}</h2>
        <div style={{ color: "#666" }}>
          Dynamic quiz for the whole subject (adaptive difficulty).
        </div>
      </div>

      <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div style={{ fontWeight: 900 }}>Progress</div>
          <div style={{ color: "#666" }}>
            Answered {answeredCount}/{total}
          </div>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="btn" onClick={start}>
            Regenerate
          </button>
          <button className="btn btn-primary" onClick={submit} disabled={total === 0}>
            Submit
          </button>
        </div>
      </div>

      {result && (
        <div className="card">
          <div style={{ fontWeight: 900 }}>Result</div>
          <div style={{ marginTop: 6 }}>
            Score: <b>{result.score}%</b> ({result.correct_answers}/{result.total_questions})
          </div>
        </div>
      )}

      {qs.length === 0 ? (
        <div className="card">
          <div style={{ fontWeight: 900 }}>No questions</div>
          <div style={{ color: "#666", marginTop: 6 }}>
            Add questions first (seed/AI) or broaden the subject question bank.
          </div>
        </div>
      ) : (
        <div style={{ display: "grid", gap: 10 }}>
          {qs.map((q, idx) => (
            <div key={q.id} className="card" style={{ display: "grid", gap: 8 }}>
              <div style={{ fontWeight: 900 }}>
                {idx + 1}. {q.prompt}
              </div>

              <div style={{ display: "grid", gap: 6 }}>
                {(q.choices || []).map((ch, i) => (
                  <label key={i} style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    <input
                      type="radio"
                      name={`q-${q.id}`}
                      checked={answers[q.id] === i}
                      onChange={() => setAnswers((prev) => ({ ...prev, [q.id]: i }))}
                    />
                    <span>{ch}</span>
                  </label>
                ))}
              </div>

              {result && (
                <div style={{ marginTop: 6, color: "#666" }}>
                  {(() => {
                    const d = (result.details || []).find((x) => x.question_id === q.id);
                    if (!d) return null;
                    return d.is_correct ? "✅ Correct" : `❌ Wrong (correct: ${d.correct_index + 1})`;
                  })()}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <Link className="btn" to={`/subject/${subjectId}`}>
          ← Back to subject
        </Link>
        <Link className="btn" to="/u/home">
          Home
        </Link>
      </div>

      <Toast message={err} onClose={() => setErr("")} />
    </div>
  );
}
