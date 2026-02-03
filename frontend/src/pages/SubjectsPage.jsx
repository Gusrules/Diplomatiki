import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api.js";
import Toast from "../components/Toast.jsx";
import InfoBox from "../components/InfoBox.jsx";
import { getUserId } from "../lib/session.js";

export default function SubjectsPage() {
  const userId = getUserId();

  const [subjects, setSubjects] = useState([]);
  const [enrolledIds, setEnrolledIds] = useState([]);
  const [err, setErr] = useState("");

  async function refresh() {
    try {
      setErr("");
      const [all, mine] = await Promise.all([
        api.listSubjects(),
        api.myEnrolledSubjectIds(userId),
      ]);
      setSubjects(all);
      setEnrolledIds(mine || []);
    } catch (e) {
      setErr(e.message);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const mySubjects = useMemo(
    () => subjects.filter((s) => enrolledIds.includes(s.id)),
    [subjects, enrolledIds]
  );

  const exploreSubjects = useMemo(
    () => subjects.filter((s) => !enrolledIds.includes(s.id)),
    [subjects, enrolledIds]
  );

  async function enroll(subjectId) {
    try {
      await api.enroll({ user_id: userId, subject_id: subjectId });
      await refresh();
    } catch (e) {
      setErr(e.message);
    }
  }

  async function unenroll(subjectId) {
    try {
      await api.unenroll({ user_id: userId, subject_id: subjectId });
      await refresh();
    } catch (e) {
      setErr(e.message);
    }
  }

  return (
    <div>
      <h2>Subjects</h2>

      <InfoBox title="Start here">
        <div>Enroll to a subject → open modules → study guides → generate questions/flashcards → take quizzes.</div>
      </InfoBox>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <div>
          <h3>My Subjects</h3>
          {mySubjects.length === 0 ? (
            <div style={{ color: "#666" }}>You are not enrolled in any subject yet.</div>
          ) : (
            <div style={{ display: "grid", gap: 10 }}>
              {mySubjects.map((s) => (
                <div key={s.id} className="card">
                  <div style={{ fontWeight: 900 }}>{s.name}</div>

                  <div style={{ display: "flex", gap: 10, marginTop: 10, flexWrap: "wrap" }}>
                    <Link className="btn btn-primary" to={`/subject/${s.id}`}>
                      Open
                    </Link>
                    <button className="btn" onClick={() => unenroll(s.id)}>
                      Unenroll
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <h3>Next up</h3>
          {exploreSubjects.length === 0 ? (
            <div style={{ color: "#666" }}>No more subjects available.</div>
          ) : (
            <div style={{ display: "grid", gap: 10 }}>
              {exploreSubjects.map((s) => (
                <div key={s.id} className="card">
                  <div style={{ fontWeight: 900 }}>{s.name}</div>
                  <div style={{ marginTop: 10 }}>
                    <button className="btn btn-primary" onClick={() => enroll(s.id)}>
                      Enroll
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <Toast message={err} onClose={() => setErr("")} />
    </div>
  );
}
