import React, { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api.js";
import Toast from "../components/Toast.jsx";

function idxToLetter(i) {
  return String.fromCharCode(65 + Number(i));
}

export default function TeacherQuestionsDistributionPage() {
  const { subjectId } = useParams();
  const [rows, setRows] = useState([]);
  const [q, setQ] = useState("");
  const [err, setErr] = useState("");

  async function load() {
    try {
      setErr("");
      const out = await api.teacherSubjectDistributions(subjectId);
      setRows(Array.isArray(out) ? out : []);
    } catch (e) {
      setErr(e.message);
      setRows([]);
    }
  }

  useEffect(() => {
    load();
  }, [subjectId]);

  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase();
    if (!s) return rows;
    return rows.filter((r) => (r.prompt || "").toLowerCase().includes(s));
  }, [rows, q]);

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
        <h2 style={{ margin: 0 }}>Answer distribution</h2>
        <Link className="btn" to={`/t/subject/${subjectId}/stats`}>← Back</Link>
      </div>

      <div className="card" style={{ display: "grid", gap: 10 }}>
        <div style={{ fontWeight: 900 }}>Filter questions</div>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search by prompt..." />
      </div>

      {filtered.length === 0 ? (
        <div className="card" style={{ color: "rgba(255,255,255,.7)" }}>
          No data yet (or no approved questions / no attempts).
        </div>
      ) : (
        <div style={{ display: "grid", gap: 10 }}>
          {filtered.map((r) => (
            <div key={r.question_id} className="card" style={{ display: "grid", gap: 10 }}>
              <div style={{ fontWeight: 900 }}>
                #{r.question_id}
              </div>

              <div style={{ color: "rgba(255,255,255,.9)", whiteSpace: "pre-wrap" }}>
                {r.prompt}
              </div>

              {/* ✅ Αφαιρέσαμε το "Answer distribution (n=...)" όπως ζήτησες */}
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                {(r.distribution || []).map((d) => (
                  <div key={d.selected_index} className="badge">
                    {idxToLetter(d.selected_index)}: {Math.round((d.pct || 0) * 100)}%
                  </div>
                ))}
              </div>

              {Number(r.total || 0) === 0 && (
                <div style={{ fontSize: 12, color: "rgba(255,255,255,.55)" }}>
                  No attempts recorded yet for this question.
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <Toast message={err} onClose={() => setErr("")} />
    </div>
  );
}
