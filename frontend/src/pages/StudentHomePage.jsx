import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api.js";
import { getUserId, getName } from "../lib/session.js";
import Toast from "../components/Toast.jsx";
import InfoBox from "../components/InfoBox.jsx";

export default function StudentHomePage() {
  const userId = getUserId();
  const name = getName();

  const [subjects, setSubjects] = useState([]);
  const [enrolledIds, setEnrolledIds] = useState([]);
  const [progress, setProgress] = useState([]);  
  const [err, setErr] = useState("");
  const [dueToday, setDueToday] = useState(null);

  async function load() {
    try {
      setErr("");

      const [all, mine, todayRows, prog] = await Promise.all([
        api.listSubjects(),
        api.myEnrolledSubjectIds(userId),
        api.reviewToday(userId),                 
        api.studentSubjectsProgress(userId),
      ]);

      setSubjects(all || []);
      setEnrolledIds(mine || []);
      setProgress(prog || []);

      const arr = Array.isArray(todayRows) ? todayRows : [];
      setDueToday(arr.length);                  
    } catch (e) {
      setErr(e.message);
    }
  }


  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const mySubjects = useMemo(
    () => subjects.filter((s) => enrolledIds.includes(s.id)),
    [subjects, enrolledIds]
  );

  const progMap = useMemo(() => {
    const m = new Map();
    (progress || []).forEach((p) => m.set(p.subject_id, p));
    return m;
  }, [progress]);

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <h2>Welcome{name ? `, ${name}` : ""}!</h2>

      <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div style={{ fontWeight: 900 }}>Daily Review</div>
          <div style={{ color: "#666" }}>{dueToday === null ? "Loading review..." : `${dueToday} questions due today (SM-2)`}</div>
        </div>
        <Link className="btn btn-primary" to="/review">
          Do your daily quiz
        </Link>
      </div>

      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <Link className="btn" to="/subjects">
          Browse subjects
        </Link>
      </div>

      <h3 style={{ marginBottom: 0 }}>My subjects</h3>
      {mySubjects.length === 0 ? (
        <div className="card">
          <div style={{ fontWeight: 900 }}>No enrollments yet</div>
          <div style={{ color: "#666", marginTop: 6 }}>
            Go to Browse subjects and press <b>Enroll</b>.
          </div>
          <div style={{ marginTop: 10 }}>
            <Link className="btn btn-primary" to="/subjects">
              Enroll to a subject
            </Link>
          </div>
        </div>
      ) : (
        <div style={{ display: "grid", gap: 10 }}>
          {mySubjects.map((s) => {
            const p = progMap.get(s.id);

            return (
              <div
                key={s.id}
                className="card"
                style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}
              >
                <div>
                  <div style={{ fontWeight: 900 }}>{s.name}</div>
                  <div style={{ color: "#666" }}>{s.description || ""}</div>

                  <div style={{ color: "#666", marginTop: 6 }}>
                    Level: <b>{p?.level?.toFixed?.(1) ?? "—"}</b> •{" "}
                    Accuracy: <b>{Math.round((p?.accuracy ?? 0) * 100)}%</b> •{" "}
                    Attempts: <b>{p?.attempts_count ?? 0}</b> •{" "}
                    Due reviews: <b>{p?.due_reviews ?? 0}</b>
                  </div>
                </div>

                <Link className="btn btn-primary" to={`/subject/${s.id}`}>
                  Open
                </Link>
              </div>
            );
          })}
        </div>
      )}

      <Toast message={err} onClose={() => setErr("")} />
    </div>
  );
}
