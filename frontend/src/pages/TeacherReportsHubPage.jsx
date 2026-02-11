import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api.js";
import InfoBox from "../components/InfoBox.jsx";

export default function TeacherReportsHubPage() {
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;

    (async () => {
      try {
        setLoading(true);
        setError("");
        const data = await api.listSubjects();
        if (mounted) setSubjects(Array.isArray(data) ? data : []);
      } catch (e) {
        if (mounted) setError(e?.message || "Failed to load subjects");
      } finally {
        if (mounted) setLoading(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div style={{ display: "grid", gap: 14 }}>
      <div>
        <h2 style={{ margin: 0 }}>Reports</h2>
        <div style={{ color: "rgba(255,255,255,.7)", marginTop: 6 }}>
          Choose a subject to view aggregated performance (attempts, accuracy, unique students).
        </div>
      </div>

      <InfoBox title="Reports overview">
        <div>• View attempts, accuracy, and unique students per subject.</div>
        <div>• Click “View statistics” to open the subject analytics page.</div>
      </InfoBox>


      {loading && <div className="card">Loading…</div>}

      {!loading && error && (
        <div className="card" style={{ border: "1px solid rgba(255,80,80,.35)" }}>
          {error}
        </div>
      )}

      {!loading && !error && (
        <div style={{ display: "grid", gap: 10 }}>
          {subjects.map((s) => (
            <div
              key={s.id}
              className="card"
              style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}
            >
              <div>
                <div style={{ fontWeight: 900 }}>{s.name}</div>
                <div style={{ color: "rgba(255,255,255,.6)" }}>{s.description || ""}</div>
              </div>

              <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                <Link className="btn btn-primary" to={`/t/subject/${s.id}/stats`}>
                  View statistics
                </Link>
              </div>
            </div>
          ))}

          {subjects.length === 0 && <div className="card">No subjects yet.</div>}
        </div>
      )}
    </div>
  );
}
