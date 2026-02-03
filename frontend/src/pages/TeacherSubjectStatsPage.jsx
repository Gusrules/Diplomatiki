import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api.js";
import Toast from "../components/Toast.jsx";

export default function TeacherSubjectStatsPage() {
  const { subjectId } = useParams();
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");

  async function load() {
    try {
      setErr("");
      const out = await api.teacherSubjectSummary(subjectId);
      setData(out);
    } catch (e) {
      setErr(e.message);
    }
  }

  useEffect(() => {
    load();
  }, [subjectId]);

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <h2>Subject statistics</h2>

      {!data ? (
        <div style={{ color: "#666" }}>Loading...</div>
      ) : (
        <div className="card" style={{ display: "grid", gap: 8 }}>
          <div style={{ fontWeight: 900 }}>{data.subject_name}</div>
          <div>Unique students: <b>{data.unique_students}</b></div>
          <div>Total attempts: <b>{data.attempts_count}</b></div>
          <div>Accuracy: <b>{Math.round((data.accuracy || 0) * 100)}%</b></div>
          <div>Total questions: <b>{data.questions_total}</b></div>
        </div>
      )}

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <Link className="btn" to={`/t/subject/${subjectId}`}>← Back</Link>
        <Link className="btn" to={`/t/subjects`}>My subjects</Link>
      </div>

      <Toast message={err} onClose={() => setErr("")} />
    </div>
  );
}
