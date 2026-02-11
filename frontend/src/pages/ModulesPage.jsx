import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../lib/api.js";
import Toast from "../components/Toast.jsx";
import InfoBox from "../components/InfoBox.jsx";
import { getRole } from "../lib/session.js";

export default function ModulesPage() {
  const { subjectId } = useParams();
  const [items, setItems] = useState([]);
  const [err, setErr] = useState("");
  const isTeacher = getRole() === "teacher";

  // Create module form (teacher only)
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  async function refresh() {
    try {
      setErr("");
      const res = await api.listModulesBySubject(subjectId);
      setItems(Array.isArray(res) ? res : []);
    } catch (e) {
      setErr(e.message);
      setItems([]);
    }
  }

  async function deleteModule(m) {
    try {
      setErr("");
      const ok = window.confirm(`Delete module "${m.title}"?`);
      if (!ok) return;

      await api.deleteModule(m.id);
      setErr("🗑️ Module deleted.");
      await refresh(); // ή load() ανάλογα πως το λέγεις
    } catch (e) {
      setErr(e.message);
    }
  }

  useEffect(() => {
    refresh();

    // keep last subject only for teacher UX
    if (isTeacher) {
      const sid = Number(subjectId);
      if (Number.isFinite(sid) && sid > 0) {
        localStorage.setItem("t_last_subject_id", String(sid));
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [subjectId]);

  async function create() {
    try {
      await api.createModule({
        subject_id: Number(subjectId),
        title: title.trim(),
        description: description.trim(),
      });
      setTitle("");
      setDescription("");
      setErr("OK: module created.");
      await refresh();
    } catch (e) {
      setErr(e.message);
    }
  }

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div>
        <h2 style={{ margin: 0 }}>Modules</h2>
        <div style={{ color: "rgba(255,255,255,.7)", marginTop: 6 }}>
          Subject #{subjectId}
        </div>
      </div>

      {/* Cleaner InfoBox */}
      <InfoBox title={isTeacher ? "Teacher workflow (quick)" : "How to use"}>
        {isTeacher ? (
          <>
            <div>• Open a module → Resources</div>
            <div>• Add Study Guide / Explanation</div>
            <div>• Generate Questions / Flashcards</div>
            <div>• Review pending questions</div>
          </>
        ) : (
          <>
            <div>• Open a module to view Resources</div>
            <div>• Practice with Adaptive Quiz</div>
            <div>• Use Flashcards for revision</div>
          </>
        )}
      </InfoBox>

      {/* Create Module (teacher only) */}
      {isTeacher && (
        <div className="card" style={{ marginBottom: 2 }}>
          <div style={{ fontWeight: 800, marginBottom: 8 }}>Create Module</div>
          <div className="grid" style={{ gap: 10 }}>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Module title"
            />
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Description (optional)"
            />
            <button className="btn btn-primary" onClick={create} disabled={!title.trim()}>
              Create
            </button>
          </div>
        </div>
      )}

      <div style={{ display: "grid", gap: 10 }}>
        {items.map((m) => (
          <div key={m.id} className="card" style={{ padding: 14 }}>
            <div style={{ fontWeight: 900 }}>{m.title}</div>
            {m.description ? (
              <div style={{ color: "rgba(255,255,255,.7)", marginTop: 4 }}>{m.description}</div>
            ) : null}
            <div
              style={{
                display: "flex",
                gap: 10,
                flexWrap: "wrap",
                alignItems: "center",
                marginTop: 10,
              }}
            >
              <Link className="btn" to={`/resources/${m.id}`}>Resources</Link>

              {isTeacher && (
                <Link className="btn" to={`/questions/module/${m.id}`}>Questions</Link>
              )}

              <Link className="btn" to={`/flashcards/${m.id}`}>Flashcards</Link>

              <Link className="btn btn-primary" to={`/adaptive/${m.id}`}>Adaptive quiz</Link>

              {isTeacher && (
                <button className="btn btn-danger" onClick={() => deleteModule(m)}>
                  Delete
                </button>
              )}
            </div>
          </div>
        ))}

        {items.length === 0 && (
          <div className="card" style={{ color: "rgba(255,255,255,.75)" }}>
            No modules yet.
          </div>
        )}
      </div>

      <Toast message={err} onClose={() => setErr("")} />
    </div>
  );
}
