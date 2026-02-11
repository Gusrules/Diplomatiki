import React, { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../lib/api.js";
import Toast from "../components/Toast.jsx";
import InfoBox from "../components/InfoBox.jsx";
import { getUserId } from "../lib/session.js";

function StatusBadge({ status }) {
  const map = {
    pending: { bg: "rgba(250,204,21,.14)", border: "rgba(250,204,21,.35)", text: "Pending" },
    approved: { bg: "rgba(34,197,94,.14)", border: "rgba(34,197,94,.35)", text: "Approved" },
    rejected: { bg: "rgba(239,68,68,.14)", border: "rgba(239,68,68,.35)", text: "Rejected" },
  };
  const s = map[status] || { bg: "rgba(255,255,255,.06)", border: "rgba(255,255,255,.12)", text: status || "?" };
  return (
    <span
      style={{
        fontSize: 12,
        fontWeight: 800,
        padding: "4px 10px",
        borderRadius: 999,
        background: s.bg,
        border: `1px solid ${s.border}`,
      }}
    >
      {s.text}
    </span>
  );
}

export default function QuestionsPage({ mode }) {
  const params = useParams();
  const teacherId = getUserId();

  const [items, setItems] = useState([]);
  const [status, setStatus] = useState("pending"); // default: pending moderation
  const [err, setErr] = useState("");

  const [editId, setEditId] = useState(null);
  const [editPrompt, setEditPrompt] = useState("");
  const [editChoices, setEditChoices] = useState(["", "", "", ""]);
  const [editCorrect, setEditCorrect] = useState(0);

  const title = useMemo(() => {
    return mode === "module"
      ? `Teacher Questions — Module #${params.moduleId}`
      : `Teacher Questions — Resource #${params.resourceId}`;
  }, [mode, params.moduleId, params.resourceId]);

  async function load() {
    try {
      setErr("");
      if (mode === "module") {
        const data = await api.listQuestionsByModuleTeacher(params.moduleId, status);
        setItems(data || []);
      } else {
        const data = await api.listQuestionsByResourceTeacher(params.resourceId, status);
        setItems(data || []);
      }
    } catch (e) {
      setErr(e.message);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, params.moduleId, params.resourceId, status]);

  function startEdit(q) {
    setEditId(q.id);
    setEditPrompt(q.prompt || "");
    setEditChoices(Array.isArray(q.choices) ? q.choices.slice(0, 4) : ["", "", "", ""]);
    setEditCorrect(Number.isFinite(q.correct_index) ? q.correct_index : 0);
  }

  function cancelEdit() {
    setEditId(null);
    setEditPrompt("");
    setEditChoices(["", "", "", ""]);
    setEditCorrect(0);
  }

  async function saveEdit() {
    try {
      setErr("");
      if (!editId) return;

      const payload = {
        prompt: editPrompt,
        choices: editChoices,
        correct_index: Number(editCorrect),
      };

      if (!payload.prompt.trim()) throw new Error("Prompt cannot be empty");
      if (!Array.isArray(payload.choices) || payload.choices.length !== 4) throw new Error("Need exactly 4 choices");
      if (payload.choices.some((c) => !String(c).trim())) throw new Error("Choices cannot be empty");
      if (payload.correct_index < 0 || payload.correct_index > 3) throw new Error("Correct index must be 0..3");

      await api.editQuestion(editId, payload);
      cancelEdit();
      await load();
      setErr("OK: saved. Question is now Approved");
    } catch (e) {
      setErr(e.message);
    }
  }

  async function approve(qid) {
    try {
      setErr("");
      await api.approveQuestion(qid, teacherId);
      await load();
    } catch (e) {
      setErr(e.message);
    }
  }

  async function reject(qid) {
    try {
      setErr("");
      await api.rejectQuestion(qid, teacherId);
      await load();
    } catch (e) {
      setErr(e.message);
    }
  }

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div>
        <h2 style={{ marginBottom: 6 }}>{title}</h2>
        <div style={{ color: "rgba(255,255,255,.7)" }}>
          Approve / reject AI questions. Editing sends the question back to <b>pending</b>.
        </div>
      </div>

      <div className="card" style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
        <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
          Status:
          <select value={status} onChange={(e) => setStatus(e.target.value)} style={{ maxWidth: 220 }}>
            <option value="pending">pending</option>
            <option value="approved">approved</option>
            <option value="rejected">rejected</option>
            <option value="all">all</option>
          </select>
        </label>
        <button className="btn" onClick={load}>Reload</button>
        <div style={{ marginLeft: "auto", color: "rgba(255,255,255,.7)" }}>
          {items.length} questions
        </div>
      </div>

      <InfoBox title="Moderation rules">
        <div>• Students should only see <b>approved</b> questions.</div>
        <div>• If you edit a question, it becomes <b>pending</b> again (needs approval).</div>
      </InfoBox>

      {items.length === 0 ? (
        <div className="card">
          <div style={{ fontWeight: 900 }}>No questions found</div>
          <div style={{ color: "rgba(255,255,255,.7)", marginTop: 6 }}>
            Try switching the status filter or generate questions from a study guide.
          </div>
        </div>
      ) : (
        <div style={{ display: "grid", gap: 10 }}>
          {items.map((q) => (
            <div key={q.id} className="card" style={{ display: "grid", gap: 10 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                <div style={{ fontWeight: 900 }}>#{q.id}</div>
                <StatusBadge status={q.status} />
                <div style={{ marginLeft: "auto", display: "flex", gap: 10, flexWrap: "wrap" }}>
                  <button className="btn" onClick={() => startEdit(q)}>Edit</button>
                  {q.status !== "approved" && (
                    <button className="btn btn-primary" onClick={() => approve(q.id)} disabled={q.status === "approved"}>
                      Approve
                    </button>
                  )}
                  {q.status !== "rejected" && (
                    <button className="btn btn-danger" onClick={() => reject(q.id)} disabled={q.status === "rejected"}>
                      Reject
                    </button>
                  )}
                </div>
              </div>

              <div style={{ fontWeight: 800 }}>{q.prompt}</div>

              <ol style={{ margin: 0, paddingLeft: 18 }}>
                {(q.choices || []).map((c, idx) => (
                  <li key={idx} style={{ opacity: 0.95 }}>
                    {c} {Number(q.correct_index) === idx ? <span style={{ opacity: 0.7 }}> (correct)</span> : null}
                  </li>
                ))}
              </ol>

              {editId === q.id && (
                <div style={{ borderTop: "1px solid rgba(255,255,255,.10)", paddingTop: 12, display: "grid", gap: 10 }}>
                  <div style={{ fontWeight: 900 }}>Edit question</div>

                  <label>
                    Prompt
                    <textarea value={editPrompt} onChange={(e) => setEditPrompt(e.target.value)} rows={3} />
                  </label>

                  <div className="grid grid-2">
                    {editChoices.map((v, i) => (
                      <label key={i}>
                        Choice {i + 1}
                        <input
                          value={v}
                          onChange={(e) =>
                            setEditChoices((prev) => {
                              const copy = [...prev];
                              copy[i] = e.target.value;
                              return copy;
                            })
                          }
                        />
                      </label>
                    ))}
                  </div>

                  <label style={{ maxWidth: 260 }}>
                    Correct choice
                    <select value={editCorrect} onChange={(e) => setEditCorrect(Number(e.target.value))}>
                      <option value={0}>1</option>
                      <option value={1}>2</option>
                      <option value={2}>3</option>
                      <option value={3}>4</option>
                    </select>
                  </label>

                  <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                    <button className="btn btn-primary" onClick={saveEdit}>Save</button>
                    <button className="btn" onClick={cancelEdit}>Cancel</button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <Toast message={err} onClose={() => setErr("")} />
    </div>
  );
}
