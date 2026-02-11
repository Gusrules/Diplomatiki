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
  const [err, setErr] = useState("");
  const [flipped, setFlipped] = useState(false);
  const [animKey, setAnimKey] = useState(0);


  useEffect(() => {
    api
      .getFlashcardsByModule(moduleId)
      .then((res) => {
        // res should be an array
        setSets(Array.isArray(res) ? res : []);
        setActiveSetIndex(0);
        setI(0);
      })
      .catch((e) => setErr(e.message));
  }, [moduleId]);

  if (!sets) return <div>Loading…</div>;

  const activeSet = sets[activeSetIndex] || null;
  const cards = activeSet?.flashcards || [];
  const card = cards[i];

  return (
    <div>
      <button
        className="btn"
        onClick={() => window.history.back()}
        style={{ marginBottom: 10 }}
      >
        ← Back to module
      </button>
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
            <div style={{ display: "flex", gap: 10, alignItems: "center", marginTop: 10 }}>
              <span className="badge">
                Flashcards
              </span>

              <div style={{ fontWeight: 800 }}>
                {activeSet.title}
              </div>

              <span className="badge">
                {cards.length} cards
              </span>
            </div>
          </div>

          {/* cards */}
          {cards.length === 0 ? (
            <div style={{ marginTop: 10 }}>This set has no flashcards.</div>
          ) : (
            <div style={{ marginTop: 16, display: "grid", gap: 12 }}>
              {/* FLIP CARD */}
              <div className="flashcard-wrap">
                <div
                  key={animKey}
                  className={`flashcard flashcard-anim ${flipped ? "is-flipped" : ""}`}
                  onClick={() => setFlipped((v) => !v)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") setFlipped((v) => !v);
                  }}
                  title="Click to flip"
                  style={{ cursor: "pointer" }}
                >
                  {/* FRONT */}
                  <div className="flashcard-face front">
                    <div className="flashcard-kicker">Front</div>
                    <div className="flashcard-text">{card?.front || ""}</div>
                    <div className="flashcard-progress" style={{ marginTop: 12 }}>
                      Card {i + 1}/{cards.length}
                    </div>
                  </div>

                  {/* BACK */}
                  <div className="flashcard-face back">
                    <div className="flashcard-kicker">Back</div>
                    <div className="flashcard-text">{card?.back || ""}</div>
                    <div className="flashcard-progress" style={{ marginTop: 12 }}>
                      Card {i + 1}/{cards.length}
                    </div>
                  </div>
                </div>
              </div>

              {/* ACTIONS */}
              <div className="flashcard-actions">
                <button className="btn" onClick={() => setFlipped((v) => !v)}>
                  {flipped ? "Show front" : "Show back"}
                </button>

                <div style={{ flex: 1 }} />

                <div className="flashcard-nav">
                  <button
                    className="btn"
                    onClick={() => {
                      setI((v) => Math.max(0, v - 1));
                      setFlipped(false);
                      setAnimKey((k) => k + 1);
                    }}
                    disabled={i === 0}
                  >
                    Prev
                  </button>

                  <button
                    className="btn btn-primary"
                    onClick={() => {
                      setI((v) => Math.min(cards.length - 1, v + 1));
                      setFlipped(false);
                      setAnimKey((k) => k + 1);
                    }}
                    disabled={i === cards.length - 1}
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>


          )}
        </>
      )}

      <Toast message={err} onClose={() => setErr("")} />
    </div>
  );
}
