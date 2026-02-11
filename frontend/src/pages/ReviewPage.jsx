import React, { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api.js";
import Toast from "../components/Toast.jsx";
import InfoBox from "../components/InfoBox.jsx";
import { getUserId } from "../lib/session.js";

export default function ReviewPage() {
  const userId = getUserId();

  const [items, setItems] = useState([]);
  const [idx, setIdx] = useState(0);

  const [selected, setSelected] = useState(null); // selected_index
  const [checked, setChecked] = useState(false);
  const [isCorrect, setIsCorrect] = useState(null);

  const [lastResult, setLastResult] = useState(null); // response from /review/submit
  const [err, setErr] = useState("");

  const current = useMemo(() => items[idx] || null, [items, idx]);

  async function load() {
    try {
      setErr("");
      if (!userId) {
        setErr("Not logged in. Go to Login.");
        return;
      }
      const data = await api.reviewToday(userId);
      const arr = Array.isArray(data) ? data : [];
      setItems(arr);
      setIdx(0);
      setSelected(null);
      setChecked(false);
      setIsCorrect(null);
      setLastResult(null);
    } catch (e) {
      setErr(e.message);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  function resetQuestionState() {
    setSelected(null);
    setChecked(false);
    setIsCorrect(null);
    setLastResult(null);
  }

  async function checkAndSubmit() {
    try {
      setErr("");
      if (!current) return;
      if (selected === null) throw new Error("Choose an answer first.");

      const correctIndex =
        current.correct_index ??
        current.correct_choice_index ??
        current.answer_index ??
        null;

      if (correctIndex === null || correctIndex === undefined) {
        throw new Error(
          "Review endpoint did not return correct_index. Add correct_index to /review/today output."
        );
      }

      const ok = Number(selected) === Number(correctIndex);
      setChecked(true);
      setIsCorrect(ok);

      const quality = ok ? 1 : 0;

      const out = await api.reviewSubmit({
        user_id: Number(userId),
        question_id: Number(current.question_id),
        quality,
      });

      setLastResult(out);
    } catch (e) {
      setErr(e.message);
    }
  }

  async function next() {
    if (idx + 1 < items.length) {
      setIdx(idx + 1);
      resetQuestionState();
      return;
    }
    // τέλος: auto-refresh για να δεις αν έμεινε κάτι due
    await load();
  }

  function fmtNextReview(v) {
    if (!v) return "-";
    try {
      const d = new Date(v);
      if (Number.isNaN(d.getTime())) return String(v);
      return d.toLocaleString();
    } catch {
      return String(v);
    }
  }

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <h2>Daily Review</h2>

      <InfoBox title="Spaced repetition (SM-2)">
        <div>Shows questions that are due (next_review ≤ today).</div>
        <div>You answer and the system updates SM-2 automatically.</div>
      </InfoBox>

      {items.length === 0 ? (
        <div className="card">
          <div style={{ fontWeight: 900 }}>No cards due today 🎉</div>
          <div style={{ color: "rgba(255,255,255,.7)", marginTop: 6 }}>
            Come back tomorrow or practice an adaptive quiz.
          </div>
        </div>
      ) : (
        <div className="card" style={{ display: "grid", gap: 10 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ fontWeight: 900 }}>
              Question {idx + 1} / {items.length}
            </div>
          </div>

          <div style={{ fontWeight: 800 }}>{current?.prompt}</div>

          <div style={{ display: "grid", gap: 8 }}>
            {(current?.choices || []).map((c, i) => (
              <label key={i} style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <input
                  type="radio"
                  name="review-choice"
                  disabled={checked}
                  checked={selected === i}
                  onChange={() => setSelected(i)}
                />
                <span>{c}</span>
              </label>
            ))}
          </div>

          {checked && (
            <div style={{ color: isCorrect ? "#16a34a" : "#ef4444", fontWeight: 800 }}>
              {isCorrect ? "✅ Correct" : "❌ Wrong"}
            </div>
          )}

          {checked && lastResult && (
            <div style={{ color: "rgba(255,255,255,.75)", fontSize: 13 }}>
              Updated: next_review_at={fmtNextReview(lastResult.next_review_at)}{" "}
              | EF={String(lastResult.easiness_factor)}{" "}
              | interval_days={String(lastResult.interval_days)}{" "}
              | reps={String(lastResult.repetitions)}{" "}
              | status={String(lastResult.status)}
            </div>
          )}

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 6 }}>
            {!checked ? (
              <button className="btn btn-primary" onClick={checkAndSubmit}>
                Check & Submit
              </button>
            ) : (
              <button className="btn btn-primary" onClick={next}>
                Next
              </button>
            )}
          </div>
        </div>
      )}

      <Toast message={err} onClose={() => setErr("")} />
    </div>
  );
}
