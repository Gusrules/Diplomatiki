import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api.js";
import Toast from "../components/Toast.jsx";

export default function SubjectResourcesPage() {
  const { subjectId } = useParams();

  const [subject, setSubject] = useState(null);
  const [modules, setModules] = useState([]);
  const [err, setErr] = useState("");

  async function load() {
    try {
      setErr("");

      const s = await api.getSubjectFromList(subjectId);
      setSubject(s);

      const mods = await api.listModulesBySubject(subjectId);
      setModules(mods || []);
    } catch (e) {
      setErr(e.message);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [subjectId]);

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div>
        <h2 style={{ marginBottom: 6 }}>{subject?.name || "Subject resources"}</h2>
        <div style={{ color: "#666" }}>
          Choose a module to view resources or flashcards.
        </div>
      </div>

      {modules.length === 0 ? (
        <div className="card">
          <div style={{ fontWeight: 900 }}>No modules yet</div>
          <div style={{ color: "#666", marginTop: 6 }}>
            This subject has no modules.
          </div>
        </div>
      ) : (
        <div style={{ display: "grid", gap: 10 }}>
          {modules.map((m) => (
            <div key={m.id} className="card" style={{ display: "grid", gap: 8 }}>
              <div style={{ fontWeight: 900 }}>{m.title}</div>
              <div style={{ color: "#666" }}>{m.description || ""}</div>

              <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 6 }}>
                <Link className="btn btn-primary" to={`/resources/${m.id}`}>
                  View resources
                </Link>
                <Link className="btn" to={`/flashcards/${m.id}`}>
                  View flashcards
                </Link>
                <Link className="btn" to={`/adaptive/${m.id}`}>
                  Take module quiz
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      <div>
        <Link className="btn" to={`/subject/${subjectId}`}>
          ← Back to subject
        </Link>
      </div>

      <Toast message={err} onClose={() => setErr("")} />
    </div>
  );
}
