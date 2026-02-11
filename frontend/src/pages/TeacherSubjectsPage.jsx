import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api.js";
import Toast from "../components/Toast.jsx";
import { getUserId } from "../lib/session.js";

export default function TeacherSubjectsPage() {
  const [subjects, setSubjects] = useState([]);
  const [err, setErr] = useState("");
  const teacherId = getUserId();
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");

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

  async function createSubject() {
    try {
      setErr("");
      await api.createSubject({ name: newName.trim(), description: newDesc.trim() });
      setNewName("");
      setNewDesc("");
      await load(); // ή refresh() ανάλογα πώς το λέγεις
    } catch (e) {
      setErr(e.message);
    }
  }

  async function deleteSubject(s) {
    try {
      setErr("");
      const ok = window.confirm(`Delete subject "${s.name}"?`);
      if (!ok) return;

      await api.deleteSubject(s.id);
      await load(); // ή refresh()
    } catch (e) {
      setErr(e.message);
    }
  }

  useEffect(() => {
    load();
  }, [teacherId]);

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <h2>My Subjects</h2>

      <div className="card" style={{ display: "grid", gap: 10 }}>
        <div style={{ fontWeight: 900 }}>Create subject</div>

        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="Subject name"
        />

        <input
          value={newDesc}
          onChange={(e) => setNewDesc(e.target.value)}
          placeholder="Description (optional)"
        />

        <button
          className="btn btn-primary"
          onClick={createSubject}
          disabled={!newName.trim()}
        >
          Create
        </button>
      </div>

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
              <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                <Link className="btn" to={`/t/subject/${s.id}/stats`} style={{ color: "#ffffff" }}>
                  View Statistics
                </Link>
                <Link className="btn btn-primary" to={`/t/subject/${s.id}`}>
                  Open
                </Link>
                <button className="btn btn-danger" onClick={() => deleteSubject(s)}>
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Toast message={err} onClose={() => setErr("")} />
    </div>
  );
}
