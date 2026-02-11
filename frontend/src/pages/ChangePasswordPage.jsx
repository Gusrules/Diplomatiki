import React, { useState } from "react";
import { api } from "../lib/api.js";
import { logout as clearSession } from "../lib/session.js";
import { useNavigate } from "react-router-dom";

export default function ChangePasswordPage() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [next2, setNext2] = useState("");
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");
  const nav = useNavigate();

  async function submit(e) {
    e.preventDefault();
    try {
      setErr("");
      setOk("");

      if (!current || !next) throw new Error("Fill all fields.");
      if (next !== next2) throw new Error("New passwords do not match.");
      if (next.length < 6) throw new Error("New password must be at least 6 characters.");

      await api.changePassword({ current_password: current, new_password: next });

      setOk("✅ Password updated. Please login again.");
      clearSession();
      nav("/login", { replace: true });
    } catch (e2) {
      setErr(e2.message);
    }
  }

  return (
    <div className="card" style={{ maxWidth: 480, margin: "40px auto", padding: 16 }}>
      <h2 style={{ marginTop: 0 }}>Change password</h2>

      <form onSubmit={submit} style={{ display: "grid", gap: 10 }}>
        <label>
          Current password:
          <input type="password" value={current} onChange={(e) => setCurrent(e.target.value)} style={{ width: "100%" }} />
        </label>

        <label>
          New password:
          <input type="password" value={next} onChange={(e) => setNext(e.target.value)} style={{ width: "100%" }} />
        </label>

        <label>
          Confirm new password:
          <input type="password" value={next2} onChange={(e) => setNext2(e.target.value)} style={{ width: "100%" }} />
        </label>

        {err && <div style={{ color: "crimson" }}>{err}</div>}
        {ok && <div style={{ color: "lightgreen" }}>{ok}</div>}

        <button className="btn btn-primary" type="submit">
          Update password
        </button>
      </form>
    </div>
  );
}
