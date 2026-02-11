import React, { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api.js";
import Toast from "../components/Toast.jsx";
import { getUserId } from "../lib/session.js";

export default function SubjectPage() {
  const { subjectId } = useParams();
  const [subject, setSubject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const userId = getUserId();
  const [modules, setModules] = useState([]);  
  const [modulesProg, setModulesProg] = useState([]);


  useEffect(() => {
    (async () => {
      try {
        setErr("");
        setLoading(true);

        const [s, mods, prog] = await Promise.all([
          api.getSubjectFromList(subjectId),
          api.listModulesBySubject(subjectId),
          api.studentModulesProgress(userId, subjectId),
        ]);

        setSubject(s || null);
        setModules(mods || []);
        setModulesProg(prog || []);
      } catch (e) {
        setErr(e.message);
        setSubject(null);
        setModules([]);
        setModulesProg([]);
      } finally {
        setLoading(false);
      }
    })();
  }, [subjectId, userId]);

  const mp = useMemo(() => {
    const m = new Map();
    (modulesProg || []).forEach((r) => m.set(r.module_id, r));
    return m;
  }, [modulesProg]);

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

        <Link className="btn btn-primary" to={`/subject/${subjectId}/quiz`}>
          Take subject quiz
        </Link>
      </div>

      <div style={{ display: "grid", gap: 10 }}>
        <h3 style={{ marginBottom: 0 }}>Modules progress</h3>

        {modules.length === 0 ? (
          <div className="card" style={{ color: "rgba(255,255,255,0.7)" }}>
            No modules found.
          </div>
        ) : (
          modules.map((m) => {
            const p = mp.get(m.id);

            return (
              <div
                key={m.id}
                className="card"
                style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}
              >
                <div>
                  <div style={{ fontWeight: 900 }}>{m.title}</div>
                  <div style={{ color: "rgba(255,255,255,0.7)", marginTop: 6 }}>
                    Progress: <b>{p?.attempted_questions ?? 0}</b>/<b>{p?.questions_total ?? 0}</b> •{" "}
                    Accuracy: <b>{Math.round((p?.accuracy ?? 0) * 100)}%</b> •{" "}
                    Due reviews: <b>{p?.due_reviews ?? 0}</b>
                  </div>
                </div>

                <Link className="btn" to={`/resources/${m.id}`}>
                  Study material
                </Link>
              </div>
            );
          })
        )}
      </div>

      <Toast message={err} onClose={() => setErr("")} />
    </div>
  );
}
