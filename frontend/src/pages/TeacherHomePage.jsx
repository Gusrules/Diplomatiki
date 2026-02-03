import React, { useMemo } from "react";
import { Link } from "react-router-dom";
import InfoBox from "../components/InfoBox.jsx";

function getLastId(key) {
  const v = localStorage.getItem(key);
  const n = v ? Number(v) : null;
  return Number.isFinite(n) && n > 0 ? n : null;
}

export default function TeacherHomePage() {
  const lastSubjectId = useMemo(() => getLastId("t_last_subject_id"), []);
  const lastModuleId = useMemo(() => getLastId("t_last_module_id"), []);

  const buildLink = lastSubjectId ? `/modules/${lastSubjectId}` : "/t/subjects";
  const questionsLink = lastModuleId ? `/questions/module/${lastModuleId}` : "/t/subjects";
  const reportsLink = lastSubjectId ? `/t/subject/${lastSubjectId}/stats` : "/t/subjects";

  return (
    <div style={{ display: "grid", gap: 14 }}>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
        <div>
          <h2 style={{ margin: 0 }}>Teacher Dashboard</h2>
          <div style={{ color: "rgba(255,255,255,.7)", marginTop: 6 }}>
            Create subjects/modules, paste study guides, generate questions & flashcards, and track stats.
          </div>
        </div>

        {lastSubjectId ? (
          <Link className="btn" to={`/t/subject/${lastSubjectId}`}>
            Continue last subject
          </Link>
        ) : (
          <Link className="btn" to="/t/subjects">
            Open my subjects
          </Link>
        )}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        {/* 1 */}
        <div className="card" style={{ display: "grid", gap: 10 }}>
          <div style={{ fontWeight: 900, fontSize: 16 }}>1) My Subjects</div>
          <div style={{ color: "rgba(255,255,255,.7)" }}>
            Create / edit subjects and manage your course structure.
          </div>
          <Link className="btn btn-primary" to="/t/subjects">
            Open My Subjects
          </Link>
        </div>

        {/* 2 */}
        <div className="card" style={{ display: "grid", gap: 10 }}>
          <div style={{ fontWeight: 900, fontSize: 16 }}>2) Build Learning Material</div>
          <div style={{ color: "rgba(255,255,255,.7)" }}>
            Subject → Modules → Resources → Study guide → AI generation.
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <Link className="btn btn-primary" to={buildLink}>
              {lastSubjectId ? "Open last subject modules" : "Choose subject"}
            </Link>
            <Link className="btn" to="/t/subjects">
              Browse subjects
            </Link>
          </div>
        </div>

        {/* 3 */}
        <div className="card" style={{ display: "grid", gap: 10 }}>
          <div style={{ fontWeight: 900, fontSize: 16 }}>3) Questions & Quizzes</div>
          <div style={{ color: "rgba(255,255,255,.7)" }}>
            Review generated questions and manage quizzes per module.
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <Link className="btn btn-primary" to={questionsLink}>
              {lastModuleId ? "Open last module questions" : "Go to a module"}
            </Link>
            <Link className="btn" to="/t/subjects">
              Pick subject
            </Link>
          </div>
        </div>

        {/* 4 */}
        <div className="card" style={{ display: "grid", gap: 10 }}>
          <div style={{ fontWeight: 900, fontSize: 16 }}>4) Reports</div>
          <div style={{ color: "rgba(255,255,255,.7)" }}>
            Student performance, accuracy, and spaced repetition indicators.
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <Link className="btn btn-primary" to={reportsLink}>
              {lastSubjectId ? "Open last subject stats" : "Choose subject for stats"}
            </Link>
            <Link className="btn" to="/t/subjects">
              Browse subjects
            </Link>
          </div>
        </div>
      </div>

      <InfoBox title="Teacher flow">
        <div><b>A.</b> Create Subject → Modules</div>
        <div><b>B.</b> In Module: create Study Guide → paste content → Save</div>
        <div><b>C.</b> Generate Questions / Flashcards → review</div>
        <div><b>D.</b> Students practice → adaptive + daily review</div>
        <div><b>E.</b> Check Stats (Reports)</div>
      </InfoBox>
    </div>
  );
}
