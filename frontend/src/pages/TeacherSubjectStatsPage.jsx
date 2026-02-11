import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api.js";
import Toast from "../components/Toast.jsx";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, BarChart, Bar } from "recharts";

function DarkTooltip({ active, payload, label, kind = "attempts" }) {
  if (!active || !payload || !payload.length) return null;

  const v = payload[0]?.value;

  const valueText =
    kind === "accuracy"
      ? `${Math.round(Number(v ?? 0) * 100)}%`
      : `${Number(v ?? 0)}`;

  const title = kind === "accuracy" ? "Accuracy" : "Attempts";

  return (
    <div
      style={{
        background: "rgba(15, 23, 42, 0.92)",
        border: "1px solid rgba(148, 163, 184, 0.25)",
        borderRadius: 12,
        padding: "10px 12px",
        boxShadow: "0 10px 30px rgba(0,0,0,.35)",
        backdropFilter: "blur(6px)",
        color: "rgba(255,255,255,.9)",
        minWidth: 160,
      }}
    >
      <div style={{ fontSize: 12, color: "rgba(255,255,255,.55)", marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
        <div style={{ fontWeight: 800 }}>{title}</div>
        <div style={{ fontWeight: 900 }}>{valueText}</div>
      </div>
    </div>
  );
}


export default function TeacherSubjectStatsPage() {
  const { subjectId } = useParams();
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [timeline, setTimeline] = useState([]);
  const [mostWrong, setMostWrong] = useState([]);
  const [mwOpen, setMwOpen] = useState(false);
  const [distMap, setDistMap] = useState({}); // { [qid]: distributionResponse }


  async function load() {
    try {
      setErr("");
      const [sum, tl] = await Promise.all([
        api.teacherSubjectSummary(subjectId),
        api.teacherSubjectTimeline(subjectId, 14),
      ]);
      setData(sum);
      setTimeline(tl.days || []);
    } catch (e) {
      setErr(e.message);
      setData(null);
      setTimeline([]);
    }
  }

  async function loadMostWrong() {
    try {
      setErr("");
      const rows = await api.teacherMostWrongQuestions(subjectId, 5);
      setMostWrong(Array.isArray(rows) ? rows : []);
      setMwOpen(true);
    } catch (e) {
      setErr(e.message);
    }
  }

  async function loadDistribution(questionId) {
    try {
      setErr("");
      const out = await api.teacherAnswerDistribution(questionId);
      setDistMap((m) => ({ ...m, [questionId]: out }));
    } catch (e) {
      setErr(e.message);
    }
  }

  function idxToLetter(i) {
    return String.fromCharCode(65 + Number(i));
  }

  useEffect(() => {
    load();
  }, [subjectId]);

  useEffect(() => {
    load(); // summary + timeline κλπ
      (async () => {
        try {
          const rows = await api.teacherMostWrongQuestions(subjectId, 5);
          setMostWrong(Array.isArray(rows) ? rows : []);
          } catch (e) {
            // μην σπάει η σελίδα αν failάρει
            console.error(e);
          }
        })();
      }, [subjectId]);

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <h2>Subject statistics</h2>

      {!data ? (
        <div style={{ color: "#666" }}>Loading...</div>
      ) : (
        <div className="card" style={{ display: "grid", gap: 8 }}>
          <div style={{ fontWeight: 900 }}>{data.subject_name}</div>
          <div>Unique students: <b>{data.unique_students}</b></div>
          <div>Total attempts: <b>{data.attempts_count}</b></div>
          <div>Accuracy: <b>{Math.round((data.accuracy || 0) * 100)}%</b></div>
          <div>Total questions: <b>{data.questions_total}</b></div>
        </div>
      )}

      {/* ✅ CHARTS */}
{Array.isArray(timeline) && timeline.length > 0 && (
  <div className="card" style={{ display: "grid", gap: 14 }}>
    <div style={{ fontWeight: 900 }}>Last 14 days</div>

    {/* Attempts per day */}
    <div style={{ height: 260 }}>
      <div style={{ fontWeight: 700, fontSize: 14, opacity: 0.85 }}>
        Attempts per day
      </div>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={timeline} barCategoryGap={14}>
          <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
          <XAxis
            dataKey="day"
            tick={{ fill: "rgba(255,255,255,0.55)", fontSize: 12 }}
            axisLine={{ stroke: "rgba(255,255,255,0.12)" }}
            tickLine={{ stroke: "rgba(255,255,255,0.12)" }}
          />
          <YAxis
            tick={{ fill: "rgba(255,255,255,0.55)", fontSize: 12 }}
            axisLine={{ stroke: "rgba(255,255,255,0.12)" }}
            tickLine={{ stroke: "rgba(255,255,255,0.12)" }}
          />
          <Tooltip cursor={{fill: "transparent"}} content={<DarkTooltip kind="attempts" />} />
          <Bar
            dataKey="attempts"
            fill="rgba(59, 130, 246, 0.85)"
            radius={[10, 10, 0, 0]}
            activeBar={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>

    {/* Accuracy per day */}
    <div style={{ height: 260 }}>
      <div style={{ fontWeight: 700, fontSize: 14, opacity: 0.85 }}>
        Accuracy per day
      </div>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={timeline}>
          <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
          <XAxis
            dataKey="day"
            tick={{ fill: "rgba(255,255,255,0.55)", fontSize: 12 }}
            axisLine={{ stroke: "rgba(255,255,255,0.12)" }}
            tickLine={{ stroke: "rgba(255,255,255,0.12)" }}
          />
          <YAxis
            domain={[0, 1]}
            tickFormatter={(v) => `${Math.round(v * 100)}%`}
            tick={{ fill: "rgba(255,255,255,0.55)", fontSize: 12 }}
            axisLine={{ stroke: "rgba(255,255,255,0.12)" }}
            tickLine={{ stroke: "rgba(255,255,255,0.12)" }}
          />
          <Tooltip content={<DarkTooltip kind="accuracy" />} />
          <Line
            type="monotone"
            dataKey="accuracy"
            stroke="rgba(34, 197, 94, 0.9)"
            strokeWidth={3}
            dot={{ r: 4, fill: "rgba(34, 197, 94, 0.9)" }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  </div>
)}
      <div className="card" style={{ display: "grid", gap: 10 }}>
        <div 
          style={{
            fontSize: 18,
            fontWeight: 900,
            letterSpacing: 0.3,
            marginBottom: 6,
          }}
        >
          Top 5 questions with most wrong answers
        </div>

        {mostWrong.length === 0 ? (
          <div style={{ color: "rgba(255,255,255,.7)" }}>No attempts yet.</div>
        ) : (
          mostWrong.map((q, i) => (
            <div key={q.question_id} style={{ borderTop: i === 0 ? "none" : "1px solid rgba(255,255,255,.08)", paddingTop: i === 0 ? 0 : 10 }}>
              <div style={{ fontWeight: 800, marginBottom: 6 }}>
                #{q.question_id} • Wrong rate: <b>{Math.round((q.wrong_rate || 0) * 100)}%</b>{" "}
                <span style={{ color: "rgba(255,255,255,.6)", fontWeight: 500 }}>
                  ({q.wrong}/{q.attempts})
                </span>
              </div>
              <div style={{ color: "rgba(255,255,255,.85)", whiteSpace: "pre-wrap" }}>{q.prompt}</div>
            </div>
          ))
        )}
      </div>
        <div
          className="card"
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: 16,
            padding: "14px 16px",
            cursor: "pointer",
            transition: "transform .15s ease, box-shadow .15s ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = "translateY(-1px)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = "translateY(0)";
          }}
        >
          {/* LEFT */}
          <div>
            <div style={{ fontWeight: 900, fontSize: 15 }}>
              View Questions %
            </div>
            <div style={{ fontSize: 13, color: "rgba(255,255,255,.65)" }}>
              See answer distribution for every question in this subject
            </div>
          </div>

          {/* RIGHT */}
          <Link
            className="btn btn-primary"
            to={`/t/questions/subject/${subjectId}/distribution`}
          >
            Open
          </Link>
        </div>


{data && (!timeline || timeline.length === 0) && (
  <div className="card" style={{ color: "rgba(255,255,255,.7)" }}>
    No activity in the last 14 days.
  </div>
)}


      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <Link className="btn" to={`/t/reports`}>← Back</Link>
        <Link className="btn" to={`/t/subjects`}>My subjects</Link>
      </div>

      <Toast message={err} onClose={() => setErr("")} />
    </div>
  );
}
