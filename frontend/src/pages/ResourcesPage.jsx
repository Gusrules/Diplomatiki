import React, { useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../lib/api.js";
import Toast from "../components/Toast.jsx";
import InfoBox from "../components/InfoBox.jsx";
import { getRole, getUserId } from "../lib/session.js";

export default function ResourcesPage() {
  const role = getRole();
  const isTeacher = role === "teacher";
  const { moduleId } = useParams();

  const [items, setItems] = useState([]);
  const [err, setErr] = useState("");
  const [selected, setSelected] = useState(null);
  const [content, setContent] = useState("");
  const [newTitle, setNewTitle] = useState("");
  const [viewerOpen, setViewerOpen] = useState(false);
  const [viewerTitle, setViewerTitle] = useState("");
  const [viewerContent, setViewerContent] = useState("");
  const [editTitle, setEditTitle] = useState("");
  const [subjectId, setSubjectId] = useState(null);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadType, setUploadType] = useState("study_guide");
  const teacherId = getUserId();
  const [isGenQuestions, setIsGenQuestions] = useState(false);
  const [isGenFlashcards, setIsGenFlashcards] = useState(false);


  const studyGuides = useMemo(
    () => items.filter((x) => x.type === "study_guide"),
    [items]
  );

  // teacher has editor panel always (right side), student does not
  const showEditor = isTeacher;

  async function refresh() {
    try {
      setErr("");
      const res = await api.listResources(moduleId);
      setItems(res || []);
    } catch (e) {
      setErr(e.message);
    }
  }

  useEffect(() => {
    refresh();

    (async () => {
      try {
        const mod = await api.getModule(moduleId);
        setSubjectId(mod.subject_id);
      } catch (e) {
        console.error(e);
      }
    })();

    const mid = Number(moduleId);
    if (Number.isFinite(mid) && mid > 0) {
      localStorage.setItem("t_last_module_id", String(mid));
    }
  }, [moduleId]);

  async function loadStudyGuideForEditing(resource) {
    try {
      setErr("");
      setSelected(resource);
      setEditTitle(resource.title || "");
      const full = await api.getResource(resource.id);
      setEditTitle(full.title || "");
      setContent(full.content || "");
    } catch (e) {
      setErr(e.message);
    }
  }

  async function uploadNewFile() {
    try {
      setErr("");
      if (!uploadFile) throw new Error("Choose a file first.");
      const title = (uploadTitle || uploadFile.name).trim();

      await api.uploadResource({
        module_id: Number(moduleId),
        type: uploadType,
        title,
        uploaded_by: teacherId,
        file: uploadFile,
      });

      setErr("✅ Uploaded.");
      setUploadFile(null);
      setUploadTitle("");
      await refresh();
    } catch (e) {
      setErr(e.message);
    }
  }

  async function saveTitle() {
    try {
      setErr("");
      if (!selected) throw new Error("Select a resource first.");
      const t = editTitle.trim();
      if (!t) throw new Error("Title cannot be empty.");
      await api.patchResourceTitle(selected.id, t);
      setErr("✅ Saved title.");
      await refresh();
    } catch (e) {
      setErr(e.message);
    }
  }

  async function deleteRes(resource) {
    try {
      setErr("");
      const ok = window.confirm(`Delete "${resource.title}"?`);
      if (!ok) return;

      await api.deleteResource(resource.id);

      // αν έσβησες αυτό που edit-άρεις, καθάρισε editor
      if (selected?.id === resource.id) {
        setSelected(null);
        setContent("");
        setEditTitle("");
      }

      setErr("🗑️ Deleted.");
      await refresh();
    } catch (e) {
      setErr(e.message);
    }
  }

    async function openViewer(resource) {
      try {
        setErr("");
        const full = await api.getResource(resource.id);
        setViewerTitle(`${full.title} (${full.type})`);
        setViewerContent(full.content || "");
        setViewerOpen(true);
      } catch (e) {
        setErr(e.message);
      }
    }

  async function saveContent() {
    try {
      setErr("");
      if (!selected) throw new Error("Select a study guide first.");
      await api.patchResourceContent(selected.id, content);
      setErr("✅ Saved study material.");
      await refresh();
    } catch (e) {
      setErr(e.message);
    }
  }

  async function generateQuestions(resourceId) {
    try {
      setErr("Generating questions… this may take a few minutes.");
      setIsGenQuestions(true);

      const out = await api.generateQuestionsFromResource({ resource_id: resourceId, n: 10 });

      setErr(`✅ Created ${out.count} questions.`);
    } catch (e) {
      setErr(e.message);
    } finally {
      setIsGenQuestions(false);
    }
  }

  async function generateFlashcards(resourceId) {
    try {
      setErr("Generating flashcards… this may take a few minutes.");
      setIsGenFlashcards(true);

      const out = await api.generateFlashcardsFromResource({ resource_id: resourceId, n: 10 });

      setErr(`✅ Created ${out.count} flashcards.`);
      await refresh(); // εδώ καλό είναι γιατί εμφανίζεις νέο resource (flashcard)
    } catch (e) {
      setErr(e.message);
    } finally {
      setIsGenFlashcards(false);
    }
  }

  async function createStudyGuide() {
    try {
      setErr("");
      const out = await api.createResource({
        module_id: Number(moduleId),
        type: "study_guide",
        title: newTitle?.trim() || `Study Guide - Module ${moduleId}`,
        file_type: "txt",
        file_path: "generated",
        uploaded_by: teacherId,
      });
      setErr(`✅ Created study guide #${out.id}.`);
      setNewTitle("");
      await refresh();
    } catch (e) {
      setErr(e.message);
    }
  }

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div>
        {/* HEADER ROW */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            gap: 16,
          }}
        >
          {/* LEFT: title + subtitle */}
          <div>
            <h2 style={{ margin: 0 }}>Resources for Module #{moduleId}</h2>
            <div style={{ color: "rgba(255,255,255,.7)", marginTop: 6 }}>
              {isTeacher
                ? "Manage study guides and generate learning content."
                : "Browse material and practice."}
            </div>
          </div>

          {/* RIGHT: back button */}
          {isTeacher && subjectId && (
            <Link
              className="btn"
              to={`/t/subject/${subjectId}`}
              style={{ whiteSpace: "nowrap" }}
            >
              ← Back to subject
            </Link>
          )}
        </div>
      </div>

      <InfoBox title={isTeacher ? "Teacher: Study material → AI" : "Student: Study material"}>
        {isTeacher ? (
          <>
            <div>• Click <span className="badge">Edit content</span> on a study guide.</div>
            <div>• Edit on the right → <b>Save material</b> → generate questions/flashcards.</div>
          </>
        ) : (
          <>
            <div>• Open resources and take quizzes generated by your teacher.</div>
            <div>• Use flashcards for quick revision.</div>
          </>
        )}
      </InfoBox>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: showEditor ? "1.1fr 0.9fr" : "1fr",
          gap: 12,
          alignItems: "start",
        }}
      >
        {/* LEFT */}
        <div style={{ display: "grid", gap: 12 }}>
          {showEditor && (
            <>
              {/* Upload card */}
              <div className="card" style={{ display: "grid", gap: 12 }}>
                <div style={{ fontWeight: 900 }}>Upload file (study material)</div>

                <div className="row">
                  <select
                    value={uploadType}
                    onChange={(e) => setUploadType(e.target.value)}
                    style={{ maxWidth: 220 }}
                  >
                    <option value="study_guide">study_guide</option>
                    <option value="explanation">explanation</option>
                  </select>

                  <input
                    value={uploadTitle}
                    onChange={(e) => setUploadTitle(e.target.value)}
                    placeholder="Title (optional)"
                  />
                </div>

                <div className="row">
                  <input
                    type="file"
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  />

                  <button className="btn btn-primary" onClick={uploadNewFile} disabled={!uploadFile}>
                    Upload
                  </button>
                </div>

                <div style={{ fontSize: 12, color: "rgba(255,255,255,.6)" }}>
                  Tip: PDFs/DOCX/TXT can be downloaded by students.
                </div>
              </div>

              {/* Create study guide card */}
              <div className="card" style={{ display: "grid", gap: 10 }}>
                <div style={{ fontWeight: 900 }}>Create Study Guide (text)</div>

                <div className="row">
                  <input
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    placeholder="Title (optional)"
                  />
                  <button className="btn btn-primary" onClick={createStudyGuide}>
                    Create
                  </button>
                </div>
              </div>
            </>
          )}


          <div style={{ display: "grid", gap: 10 }}>
            <h3 style={{ margin: 0 }}>{isTeacher ? "Resources List" : "Available Material"}</h3>

            {items.length === 0 ? (
              <div className="card" style={{ color: "rgba(255,255,255,.7)" }}>
                No resources yet.
              </div>
            ) : (
              items.map((r) => {
                const hasDownload =
                  typeof r.file_path === "string" &&
                  r.file_path.trim() !== "" &&
                  r.file_path !== "generated";

                return (
                  <div key={r.id} className="card" style={{ display: "grid", gap: 10 }}>
                    <div style={{ fontWeight: 900 }}>
                      {r.title}
                      <span style={{ marginLeft: 10, fontSize: 12, color: "rgba(255,255,255,.55)" }}>
                        {r.type}
                      </span>
                    </div>

                    {showEditor && (
                      <div style={{ fontSize: 12, color: "rgba(255,255,255,.55)" }}>
                        file_type: {r.file_type} | file_path: {r.file_path}
                      </div>
                    )}

                    <div className="row">
                      {showEditor && (r.type === "study_guide" || r.type === "explanation") && (
                        <button className="btn" onClick={() => loadStudyGuideForEditing(r)}>
                          Edit content
                        </button>
                      )}

                      {(r.type === "study_guide" || r.type === "explanation") && (
                        <button className="btn" onClick={() => openViewer(r)}>
                          View
                        </button>
                      )}

                      {r.type === "flashcard" && (
                        <Link className="btn" to={`/flashcards/${moduleId}`}>
                          View flashcards
                        </Link>
                      )}

                      {hasDownload && (
                        <a
                          className="btn"
                          href={`${import.meta.env.VITE_API_BASE}/resources/${r.id}/download`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Download
                        </a>
                      )}

                      {showEditor && (
                        <button className="btn btn-danger" onClick={() => deleteRes(r)}>
                          Delete
                        </button>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* ✅ bottom actions: NOT a huge card */}
          <div className="row" style={{ marginTop: 6 }}>
            {showEditor && (
              <Link className="btn" to={`/questions/module/${moduleId}`}>
                View all questions (module)
              </Link>
            )}
            <Link className="btn btn-primary" to={`/adaptive/${moduleId}`}>
              Start Adaptive Quiz
            </Link>
          </div>
        </div>

        {/* RIGHT: editor */}
        {showEditor && (
          <div style={{ display: "grid", gap: 10 }}>
            <h3 style={{ margin: 0 }}>Study Guide editor</h3>

            {studyGuides.length === 0 ? (
              <div style={{ color: "rgba(255,255,255,.7)" }}>No study_guide resources found.</div>
            ) : !selected ? (
              <div style={{ color: "rgba(255,255,255,.7)" }}>
                Select a <span className="badge">study_guide</span> from the list to edit.
              </div>
            ) : (
              <div className="card" style={{ display: "grid", gap: 10 }}>
                <div style={{ fontWeight: 900 }}>
                  Editing: {selected.title}
                  <span style={{ marginLeft: 10, fontSize: 12, color: "rgba(255,255,255,.55)" }}>
                    #{selected.id}
                  </span>
                </div>

                <div className="row">
                  <input
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    placeholder="Resource title"
                  />
                  <button className="btn" onClick={saveTitle} disabled={!editTitle.trim()}>
                    Save title
                  </button>
                </div>

                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  rows={14}
                  placeholder="Paste study material here…"
                />

                {/* ✅ RIGHT BUTTONS */}
                <div className="row">
                  <button className="btn btn-primary" onClick={saveContent} disabled={!content.trim()}>
                    Save material
                  </button>

                  <button
                    className="btn"
                    onClick={() => generateQuestions(selected.id)}
                    disabled={!content.trim() || isGenQuestions || isGenFlashcards}
                  >
                    {isGenQuestions ? "Generating questions..." : "Generate questions"}
                  </button>

                  <button
                    className="btn"
                    onClick={() => generateFlashcards(selected.id)}
                    disabled={!content.trim() || isGenFlashcards || isGenQuestions}
                  >
                    {isGenFlashcards ? "Generating flashcards..." : "Generate flashcards"}
                  </button>
                  {(isGenQuestions || isGenFlashcards) && (
                    <div style={{ fontSize: 12, color: "rgba(255,255,255,.7)" }}>
                      {isGenQuestions && "⏳ Generating questions… this may take a few minutes."}
                      {isGenFlashcards && "⏳ Generating flashcards… this may take a few minutes."}
                    </div>
                  )}
                </div>

                {/* optional helper */}
                <div style={{ fontSize: 12, color: "rgba(255,255,255,.55)" }}>
                  Tip: Save first → then generate, so the AI uses the latest content.
                </div>
              </div>
            )}
          </div>
        )}
      </div>
            {viewerOpen && (
              <div
                onClick={() => setViewerOpen(false)}
                style={{
                  position: "fixed",
                  inset: 0,
                  background: "rgba(0,0,0,.55)",
                  display: "grid",
                  placeItems: "center",
                  zIndex: 1000,
                  padding: 16,
                }}
              >
                <div
                  className="card"
                  onClick={(e) => e.stopPropagation()}
                  style={{ width: "min(900px, 100%)", maxHeight: "80vh", overflow: "auto" }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center" }}>
                    <div style={{ fontWeight: 900 }}>{viewerTitle}</div>
                    <button className="btn" onClick={() => setViewerOpen(false)}>
                      Close
                    </button>
                  </div>

                  <div style={{ marginTop: 12, whiteSpace: "pre-wrap", color: "rgba(255,255,255,.85)" }}>
                    {viewerContent?.trim() ? viewerContent : "No content yet."}
                  </div>
                </div>
              </div>
            )}

      <Toast message={err} onClose={() => setErr("")} />
    </div>
  );
}
