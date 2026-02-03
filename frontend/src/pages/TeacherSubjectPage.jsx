import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api.js";
import Toast from "../components/Toast.jsx";

export default function TeacherSubjectPage() {
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
    const sid = Number(subjectId);
    if (Number.isFinite(sid) && sid > 0) {
      localStorage.setItem("t_last_subject_id", String(sid));
    }
  }, [subjectId]);

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div>
        <h2 style={{ marginBottom: 6 }}>{subject?.name || "Subject"}</h2>
        <div style={{ color: "#666" }}>{subject?.description || ""}</div>
      </div>

      <div className="card" style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <Link className="btn btn-primary" to={`/t/subject/${subjectId}/stats`}>
          View statistics
        </Link>

        {/* Reuse existing ModulesPage (θα το ανοίξουμε και για teacher στο routing) */}
        <Link className="btn" to={`/modules/${subjectId}`}>
          Open modules (manage)
        </Link>

        <Link className="btn" to={`/t/subjects`}>
          ← Back
        </Link>
      </div>

      <h3 style={{ marginBottom: 0 }}>Modules</h3>
      {modules.length === 0 ? (
        <div style={{ color: "#666" }}>No modules yet.</div>
      ) : (
        <div style={{ display: "grid", gap: 10 }}>
          {modules.map((m) => (
            <div key={m.id} className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ fontWeight: 900 }}>{m.title}</div>
                <div style={{ color: "#666" }}>{m.description || ""}</div>
              </div>
              <Link className="btn" to={`/resources/${m.id}`}>
                Open
              </Link>
            </div>
          ))}
        </div>
      )}

      <Toast message={err} onClose={() => setErr("")} />
    </div>
  );
}
