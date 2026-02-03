import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api.js";
import Toast from "../components/Toast.jsx";
import { getUserId } from "../lib/session.js";

export default function TeacherSubjectsPage() {
  const [subjects, setSubjects] = useState([]);
  const [err, setErr] = useState("");
  const teacherId = getUserId();

  async function load() {
    try {
      setErr("");
      if (!teacherId) throw new Error("Not logged in");
      const all = await api.teacherSubjects(teacherId);
      setSubjects(all || []);
    } catch (e) {
      setErr(e.message);
      setSubjects([]);
    }
  }

  useEffect(() => {
    load();
  }, [teacherId]);

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <h2>My Subjects</h2>

      {subjects.length === 0 ? (
        <div className="card">
          <div style={{ fontWeight: 900 }}>No subjects yet</div>
          <div style={{ color: "#666", marginTop: 6 }}>
            Assign a subject to this teacher (dev) and reload.
          </div>
          <button className="btn" onClick={load} style={{ marginTop: 10 }}>
            Reload
          </button>
        </div>
      ) : (
        <div style={{ display: "grid", gap: 10 }}>
          {subjects.map((s) => (
            <div
              key={s.id}
              className="card"
              style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}
            >
              <div>
                <div style={{ fontWeight: 900 }}>{s.name}</div>
                <div style={{ color: "#666" }}>{s.description || ""}</div>
              </div>
              <Link className="btn btn-primary" to={`/t/subject/${s.id}`}>
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
