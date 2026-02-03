import React, { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../lib/api.js";
import Toast from "../components/Toast.jsx";
import InfoBox from "../components/InfoBox.jsx";

export default function FlashcardsPage() {
  const { moduleId } = useParams();

  // backend returns: list[FlashcardSetOut]
  const [sets, setSets] = useState(null);
  const [activeSetIndex, setActiveSetIndex] = useState(0);

  const [i, setI] = useState(0);
  const [showBack, setShowBack] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .getFlashcardsByModule(moduleId)
      .then((res) => {
        // res should be an array
        setSets(Array.isArray(res) ? res : []);
        setActiveSetIndex(0);
        setI(0);
        setShowBack(false);
      })
      .catch((e) => setErr(e.message));
  }, [moduleId]);

  if (!sets) return <div>Loading…</div>;

  const activeSet = sets[activeSetIndex] || null;
  const cards = activeSet?.flashcards || [];
  const card = cards[i];

  return (
    <div>
      <h2>Flashcards — Module #{moduleId}</h2>

      <InfoBox title="Flashcards">
        <div>These are generated from the selected study material.</div>
        <div>Use them for quick revision before Review (SM-2).</div>
      </InfoBox>


      {sets.length === 0 ? (
        <div style={{ marginTop: 10 }}>No flashcard sets for this module.</div>
      ) : (
        <>
          {/* choose set */}
          <div style={{ marginTop: 10, display: "flex", gap: 10, flexWrap: "wrap" }}>
            <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
              Set:
              <select
                value={activeSetIndex}
                onChange={(e) => {
                  const idx = Number(e.target.value);
                  setActiveSetIndex(idx);
                  setI(0);
                  setShowBack(false);
                }}
              >
                {sets.map((s, idx) => (
                  <option key={s.resource_id} value={idx}>
                    #{s.resource_id} — {s.title} ({s.flashcards?.length || 0} cards)
                  </option>
                ))}
              </select>
            </label>
          </div>

          {/* header */}
          <div style={{ color: "#666", marginTop: 6 }}>
            resource_id: {activeSet.resource_id} — {activeSet.title}
          </div>

          {/* cards */}
          {cards.length === 0 ? (
            <div style={{ marginTop: 10 }}>This set has no flashcards.</div>
          ) : (
            <div style={{ marginTop: 16 }}>
              <div style={{ border: "1px solid #eee", borderRadius: 12, padding: 18, minHeight: 140 }}>
                <div style={{ fontWeight: 800, marginBottom: 8 }}>
                  Card {i + 1}/{cards.length}
                </div>
                <div style={{ fontSize: 18 }}>{showBack ? card.back : card.front}</div>
              </div>

              <div style={{ display: "flex", gap: 10, marginTop: 10, flexWrap: "wrap" }}>
                <button onClick={() => setShowBack((v) => !v)}>{showBack ? "Show front" : "Show back"}</button>

                <button
                  onClick={() => {
                    setI((v) => Math.max(0, v - 1));
                    setShowBack(false);
                  }}
                  disabled={i === 0}
                >
                  Prev
                </button>

                <button
                  onClick={() => {
                    setI((v) => Math.min(cards.length - 1, v + 1));
                    setShowBack(false);
                  }}
                  disabled={i === cards.length - 1}
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}

      <Toast message={err} onClose={() => setErr("")} />
    </div>
  );
}
