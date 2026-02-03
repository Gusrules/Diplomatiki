import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../lib/api.js";
import Toast from "../components/Toast.jsx";
import InfoBox from "../components/InfoBox.jsx";
import { getUserId } from "../lib/session.js";

export default function AdaptiveQuizPage() {
  const { moduleId } = useParams();

  const userId = getUserId();          // ✅ no input
  const [n, setN] = useState(5);       // μπορείς να το αφήσεις input
  const [quizId, setQuizId] = useState(null); // ✅ comes from backend

  const [qs, setQs] = useState([]);
  const [answers, setAnswers] = useState({}); // { [questionId]: selected_index }
  const [err, setErr] = useState("");
  const [result, setResult] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  async function load() {
    // 1) find subjectId from module
      const mod = await api.getModule(moduleId);
      const subjectId = mod.subject_id;

      // 2) create session (returns quiz_id + questions)
      const sess = await api.getAdaptiveQuizSession({ userId, subjectId, moduleId: Number(moduleId), n });

      setQuizId(sess.quiz_id);
      setQs(Array.isArray(sess.questions) ? sess.questions : []);
      setAnswers({});
      setResult(null);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [moduleId]);

  async function submit() {
    if (!qs.length) {
      setErr("No questions loaded.");
      return;
    }
    if (!quizId) {
      setErr("Quiz id not loaded yet.");
      return;
    }

    const missing = qs.filter((q) => answers[q.id] === undefined);
    if (missing.length > 0) {
      setErr("Please select an option (A/B/C/D) for every question before submitting.");
      return;
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
      // ✅ δεν κάνουμε load() εδώ
    } catch (e) {
      setErr(e.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div>
      <h2>Adaptive Quiz — Module #{moduleId}</h2>

      <InfoBox title="Adaptive quiz">
        <div>Questions are selected based on your current skill level and difficulty_score.</div>
        <div>Submitting updates difficulty + user level, affecting the next selection.</div>
      </InfoBox>

      {result && (
        <div className="card" style={{ marginBottom: 12 }}>
          <div style={{ fontWeight: 900, marginBottom: 6 }}>Result</div>
          <div>Score: {result.score}%</div>
          <div>
            Correct: {result.correct_answers}/{result.total_questions}
          </div>

          <div style={{ marginTop: 10 }}>
            <button className="btn btn-primary" onClick={load}>
              Next questions
            </button>
          </div>
        </div>
      )}

      <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap", marginBottom: 12 }}>
        <div style={{ color: "#666" }}>
          user_id: <b>{userId}</b>
          {quizId ? (
            <>
              {" "}• quiz_id: <b>{quizId}</b>
            </>
          ) : null}
        </div>

        <label>
          n:{" "}
          <input
            type="number"
            value={n}
            onChange={(e) => setN(Number(e.target.value))}
            style={{ width: 70 }}
            min={1}
            max={50}
          />
        </label>

        <button className="btn" onClick={load} disabled={isLoading}>
          {isLoading ? "Loading..." : "Reload"}
        </button>

        <button className="btn btn-primary" onClick={submit} disabled={qs.length === 0 || isSubmitting || !quizId}>
          {isSubmitting ? "Submitting..." : "Submit"}
        </button>
      </div>

      {qs.length === 0 ? (
        <div style={{ color: "#666" }}>No questions loaded yet.</div>
      ) : (
        <div style={{ display: "grid", gap: 10 }}>
          {qs.map((q) => (
            <div key={q.id} className="card">
              <div style={{ fontWeight: 900, marginBottom: 8 }}>
                {q.prompt}
              </div>

              <div style={{ display: "grid", gap: 8 }}>
                {(q.choices || []).map((c, idx) => (
                  <label key={idx} style={{ display: "flex", gap: 10, alignItems: "center" }}>
                    <input
                      type="radio"
                      name={`q-${q.id}`}
                      checked={answers[q.id] === idx}
                      onChange={() => setAnswers((a) => ({ ...a, [q.id]: idx }))}
                    />
                    <span style={{ fontWeight: 900 }}>{String.fromCharCode(65 + idx)}.</span>
                    <span>{c}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <Toast message={err} onClose={() => setErr("")} />
    </div>
  );
}
