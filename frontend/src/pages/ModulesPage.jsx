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

  // Create module form
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  async function refresh() {
    try {
      const res = await api.listModulesBySubject(subjectId);
      setItems(res);
    } catch (e) {
      setErr(e.message);
    }
  }

  useEffect(() => {
    refresh();
      const sid = Number(subjectId);
      if (Number.isFinite(sid) && sid > 0) {
        localStorage.setItem("t_last_subject_id", String(sid));
      }
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
    <div>
      <h2>Modules for Subject #{subjectId}</h2>
      <p style={{ color: "#666" }}>Click module to open resources/questions/flashcards/adaptive.</p>

      <InfoBox title="How to use">
        <div>1) Create/Open a module → Resources.</div>
        <div>2) Paste study material (study guide) and press PATCH.</div>
        <div>3) Generate Questions / Flashcards.</div>
        <div>4) Use Adaptive quiz and Review to learn.</div>
      </InfoBox>

      {/* Create Module */}
      {isTeacher && (
      <div className="card" style={{ marginBottom: 12 }}>
        <div style={{ fontWeight: 800, marginBottom: 8 }}>Create Module</div>
        <div className="grid" style={{ gap: 10 }}>
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Module title" />
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
          <div key={m.id} style={{ border: "1px solid #eee", borderRadius: 12, padding: 12 }}>
            <div style={{ fontWeight: 700 }}>{m.title}</div>
            <div style={{ color: "#666" }}>{m.description || ""}</div>

            <div style={{ display: "flex", gap: 12, marginTop: 10, flexWrap: "wrap" }}>
              <Link to={`/resources/${m.id}`}>Resources</Link>
              {isTeacher && <Link to={`/questions/module/${m.id}`}>Questions</Link>}
              <Link to={`/flashcards/${m.id}`}>Flashcards</Link>
              <Link to={`/adaptive/${m.id}`}>Adaptive quiz</Link>
            </div>
          </div>
        ))}
      </div>

      <Toast message={err} onClose={() => setErr("")} />
    </div>
  );
}
