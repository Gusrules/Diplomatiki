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

const reportsLink = "/t/reports";

  return (
    <div style={{ display: "grid", gap: 14 }}>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
        <div>
          <h2 style={{ margin: 0 }}>Teacher Dashboard</h2>
          <div style={{ color: "rgba(255,255,255,.7)", marginTop: 6 }}>
            Create subjects/modules, paste study guides, generate questions & flashcards, and track stats.
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <div className="card" style={{ display: "grid", gap: 10 }}>
          <div style={{ fontWeight: 900, fontSize: 16 }}>My subjects</div>
          <div style={{ color: "rgba(255,255,255,.7)" }}>
            Create subjects, modules and learning resources. Approve / reject AI-generated questions.
          </div>
          <Link className="btn btn-primary" to="/t/subjects">
            Open My Subjects
          </Link>
        </div>

        <div className="card" style={{ display: "grid", gap: 10 }}>
          <div style={{ fontWeight: 900, fontSize: 16 }}>Reports</div>
          <div style={{ color: "rgba(255,255,255,.7)" }}>
            View student performance, accuracy per module, and overall engagement.
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <Link className="btn btn-primary" to={reportsLink}>
              View statistics
            </Link>
            {!lastSubjectId && (
              <Link className="btn" to="/t/subjects">
                Browse subjects
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
