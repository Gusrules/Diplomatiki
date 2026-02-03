import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api.js";
import Toast from "../components/Toast.jsx";

export default function SubjectPage() {
  const { subjectId } = useParams();
  const [subject, setSubject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    (async () => {
      try {
        setErr("");
        setLoading(true);
        const s = await api.getSubjectFromList(subjectId);
        setSubject(s || null);
      } catch (e) {
        setErr(e.message);
        setSubject(null);
      } finally {
        setLoading(false);
      }
    })();
  }, [subjectId]);

  if (loading) {
    return <div className="card">Loading subject…</div>;
  }

  if (!subject) {
    return (
      <div style={{ display: "grid", gap: 12 }}>
        <div className="card">
          <div style={{ fontWeight: 900 }}>Subject not found</div>
          <div style={{ color: "rgba(255,255,255,0.7)", marginTop: 6 }}>
            Maybe the subject id is invalid.
          </div>
        </div>
        <Link className="btn" to="/subjects">← Back to Subjects</Link>
        <Toast message={err} onClose={() => setErr("")} />
      </div>
    );
  }

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div>
        <h2 style={{ marginBottom: 6 }}>{subject.name}</h2>
        <div style={{ color: "rgba(255,255,255,0.7)" }}>{subject.description || ""}</div>
      </div>

      <div className="card" style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <Link className="btn" to="/subjects">← Back</Link>

        <Link className="btn" to={`/modules/${subjectId}`}>
          Modules
        </Link>

        <Link className="btn btn-primary" to={`/subject/${subjectId}/resources`}>
          Resources
        </Link>

        <Link className="btn btn-primary" to={`/subject/${subjectId}/quiz`}>
          Take subject quiz
        </Link>
      </div>

      <Toast message={err} onClose={() => setErr("")} />
    </div>
  );
}
