import { getToken } from "./session.js";

const BASE = import.meta.env.VITE_API_BASE;

async function request(path, options = {}) {
  const token = getToken();

  const res = await fetch(`${BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
    ...options,
  });

  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }

  if (!res.ok) {
    const msg =
      (data && data.detail && (typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail))) ||
      `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

export const api = {

  login: ({ role, email, password }) =>
    request(`/auth/login`, { method: "POST", body: JSON.stringify({ role, email, password }) }),


me: () => request(`/auth/me`),
logout: () => request(`/auth/logout`, { method: "POST" }),

  // subjects
  listSubjects: () => request(`/subjects/`),

    getSubjectFromList: async (subjectId) => {
    const all = await request(`/subjects/`);
    const id = Number(subjectId);
    return (all || []).find((s) => s.id === id) || null;
  },


  // modules
  listModulesBySubject: (subjectId) => request(`/modules/?subject_id=${subjectId}`),
  getModule: (moduleId) => request(`/modules/${moduleId}`),
  createModule: ({ subject_id, title, description = "" }) =>
    request(`/modules/`, {
      method: "POST",
      body: JSON.stringify({ subject_id, title, description }),
    }),

  // resources
  listResources: (moduleId) => request(`/resources/?module_id=${moduleId}`),
  getResource: (resourceId) => request(`/resources/${resourceId}`),
  createResource: ({ module_id, type, title, file_path = "generated", file_type = "txt", uploaded_by = 1 }) =>
    request(`/resources/`, {
      method: "POST",
      body: JSON.stringify({ module_id, type, title, file_path, file_type, uploaded_by }),
    }),
  patchResourceContent: (resourceId, content) =>
    request(`/resources/${resourceId}/content`, {
      method: "PATCH",
      body: JSON.stringify({ content }),
    }),

  // questions
  // Teacher lists (with status filter)
  listQuestionsByModuleTeacher: (moduleId, status = "all") =>
    request(`/questions/module/${moduleId}/teacher?status=${status}`),

  listQuestionsByResourceTeacher: (resourceId, status = "all") =>
    request(`/questions/resource/${resourceId}/teacher?status=${status}`),

  // approve/reject/edit
  approveQuestion: (questionId, teacherId) =>
    request(`/questions/${questionId}/approve?teacher_id=${teacherId}`, { method: "POST" }),

  rejectQuestion: (questionId, teacherId) =>
    request(`/questions/${questionId}/reject?teacher_id=${teacherId}`, { method: "POST" }),

  editQuestion: (questionId, payload) =>
    request(`/questions/${questionId}`, { method: "PATCH", body: JSON.stringify(payload) }),


  // AI
  generateQuestionsFromResource: ({ resource_id, n = 10 }) =>
    request(`/ai/generate-from-resource`, {
      method: "POST",
      body: JSON.stringify({ resource_id, n }),
    }),
  generateFlashcardsFromResource: ({ resource_id, n = 10 }) =>
    request(`/ai/generate-flashcards-from-resource`, {
      method: "POST",
      body: JSON.stringify({ resource_id, n }),
    }),

  // flashcards
  getFlashcardsByModule: (moduleId) => request(`/flashcards/module/${moduleId}`),

  // adaptive quiz

  getAdaptiveQuizSession: async ({ userId, subjectId, moduleId = null, n = 5 }) => {
    const mod = moduleId ? `&module_id=${moduleId}` : "";
    return request(`/adaptive-quiz/session?user_id=${userId}&subject_id=${subjectId}${mod}&n=${n}`);
  },

  getQuizByModule: (moduleId) => request(`/quizzes/by-module/${moduleId}`),

  getAdaptiveQuiz: async ({ moduleId, userId = 1, n = 5 }) => {
    const mod = await request(`/modules/${moduleId}`);
    const subjectId = mod.subject_id;
    return request(`/adaptive-quiz/next?user_id=${userId}&subject_id=${subjectId}&module_id=${moduleId}&n=${n}`);
  },

  myEnrolledSubjectIds: (userId) => request(`/enrollments/my-subjects?user_id=${userId}`),
  enroll: ({ user_id, subject_id }) =>
    request(`/enrollments/`, { method: "POST", body: JSON.stringify({ user_id, subject_id }) }),
  unenroll: ({ user_id, subject_id }) =>
    request(`/enrollments/?user_id=${user_id}&subject_id=${subject_id}`, { method: "DELETE" }),

  // attempts
  submitAttempt: (payload) => request(`/attempts/submit`, { method: "POST", body: JSON.stringify(payload) }),
  submitAttemptAnswers: (payload) =>
    request(`/attempts/submit-answers`, { method: "POST", body: JSON.stringify(payload) }),

  // review
  reviewToday: (userId) => request(`/review/today?user_id=${userId}`),
  reviewSubmit: (payload) => request(`/review/submit`, { method: "POST", body: JSON.stringify(payload) }),

  // stats
  teacherSubjectSummary: (subjectId) => request(`/reports/teacher/subject/${subjectId}/summary`),

  //teacherSubjects
  teacherSubjects: (teacherId) => request(`/subjects/teacher?teacher_id=${teacherId}`),

  //review
  reviewSummary: (userId) => request(`/reports/student/${userId}/review-summary`),
};
