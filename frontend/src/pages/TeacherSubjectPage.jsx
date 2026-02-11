import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api.js";
import Toast from "../components/Toast.jsx";

export default function TeacherSubjectPage() {
  const { subjectId } = useParams();
  const [subject, setSubject] = useState(null);
  const [modules, setModules] = useState([]);
  const [err, setErr] = useState("");
  const [accessMode, setAccessMode] = useState("public");
  const [inviteCode, setInviteCode] = useState("");

  async function load() {
    try {
      setErr("");
      const s = await api.getSubjectFromList(subjectId);
      setSubject(s);
      const mode = (s?.access_mode || "public").toLowerCase();
      setAccessMode(mode);
      setInviteCode(s?.invite_code || "");
      const mods = await api.listModulesBySubject(subjectId);
      setModules(mods || []);
    } catch (e) {
      setErr(e.message);
    }
  }

  async function saveAccess() {
    try {
      setErr("");
      const payload = { access_mode: accessMode };
      if (accessMode === "invite") payload.invite_code = inviteCode.trim() || null;

      const out = await api.updateSubjectAccess(subjectId, payload);

      setSubject(out);
      setAccessMode((out.access_mode || "public").toLowerCase());
      setInviteCode(out.invite_code || "");
      setErr("✅ Access settings saved.");
    } catch (e) {
      setErr(e.message);
    }
  }

  function genCode() {
    // απλό client-side generate (ή άστο στο backend)
    const code = Math.random().toString(36).slice(2, 10).toUpperCase();
    setInviteCode(code);
  }

  useEffect(() => {
    load();
    const sid = Number(subjectId);
    if (Number.isFinite(sid) && sid > 0) {
      localStorage.setItem("t_last_subject_id", String(sid));
    }
  }, [subjectId]);

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div>
        <h2 style={{ marginBottom: 6 }}>{subject?.name || "Subject"}</h2>
        <div style={{ color: "#666" }}>{subject?.description || ""}</div>
      </div>

      <div className="card" style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <Link className="btn btn-primary" to={`/t/subject/${subjectId}/stats`}>
          View statistics
        </Link>

        {/* Reuse existing ModulesPage (θα το ανοίξουμε και για teacher στο routing) */}
        <Link className="btn" to={`/modules/${subjectId}`}>
          Open modules (manage)
        </Link>

        <Link className="btn" to={`/t/subjects`}>
          ← Back
        </Link>
      </div>

      <div className="card" style={{ display: "grid", gap: 10 }}>
        <div style={{ fontWeight: 900 }}>Access settings</div>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ fontSize: 12, color: "rgba(255,255,255,.65)" }}>Mode</span>
            <select value={accessMode} onChange={(e) => setAccessMode(e.target.value)}>
              <option value="public">public</option>
              <option value="private">private</option>
              <option value="invite">invite</option>
            </select>
          </label>

          {accessMode === "invite" && (
            <label style={{ display: "grid", gap: 6 }}>
              <span style={{ fontSize: 12, color: "rgba(255,255,255,.65)" }}>Invite code</span>
              <input value={inviteCode} onChange={(e) => setInviteCode(e.target.value)} placeholder="Code" />
            </label>
          )}
        </div>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          {accessMode === "invite" && (
            <button className="btn" onClick={genCode}>
              Generate code
            </button>
          )}
          <button className="btn btn-primary" onClick={saveAccess}>
            Save
          </button>
        </div>
      </div>

      <Toast message={err} onClose={() => setErr("")} />
    </div>
  );
}
