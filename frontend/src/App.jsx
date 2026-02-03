import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import { RequireAuth, RequireRole } from "./components/Guards.jsx";

import SubjectsPage from "./pages/SubjectsPage.jsx";
import ModulesPage from "./pages/ModulesPage.jsx";
import ResourcesPage from "./pages/ResourcesPage.jsx";
import QuestionsPage from "./pages/QuestionsPage.jsx";
import FlashcardsPage from "./pages/FlashcardsPage.jsx";
import AdaptiveQuizPage from "./pages/AdaptiveQuizPage.jsx";
import ReviewPage from "./pages/ReviewPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import StudentHomePage from "./pages/StudentHomePage.jsx";
import TeacherHomePage from "./pages/TeacherHomePage.jsx";
import SubjectPage from "./pages/SubjectPage.jsx";

import { getRole } from "./lib/session.js";

import SubjectResourcesPage from "./pages/SubjectResourcesPage.jsx";
import SubjectQuizPage from "./pages/SubjectQuizPage.jsx";
import TeacherSubjectsPage from "./pages/TeacherSubjectsPage.jsx";
import TeacherSubjectPage from "./pages/TeacherSubjectPage.jsx";
import TeacherSubjectStatsPage from "./pages/TeacherSubjectStatsPage.jsx";

function RoleLanding() {
  const role = getRole();
  if (role === "teacher") return <Navigate to="/t/home" replace />;
  if (role === "student") return <Navigate to="/u/home" replace />;
  return <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Layout>
      <Routes>
          <Route path="/" element={<RoleLanding />} />
          <Route path="/login" element={<LoginPage />} />

          {/* Student protected */}
          <Route
            path="/u/home"
            element={
              <RequireRole role="student">
                <StudentHomePage />
              </RequireRole>
            }
          />

          <Route
            path="/subjects"
            element={
              <RequireRole role="student">
                <SubjectsPage />
              </RequireRole>
            }
          />

          <Route
            path="/subject/:subjectId"
            element={
              <RequireRole role="student">
                <SubjectPage />
              </RequireRole>
            }
          />

          <Route
            path="/subject/:subjectId/resources"
            element={
              <RequireRole role="student">
                <SubjectResourcesPage />
              </RequireRole>
            }
          />

          <Route
            path="/subject/:subjectId/quiz"
            element={
              <RequireRole role="student">
                <SubjectQuizPage />
              </RequireRole>
            }
          />

          <Route
            path="/modules/:subjectId"
            element={
              <RequireAuth>
                <ModulesPage />
              </RequireAuth>
            }
          />

          <Route
            path="/resources/:moduleId"
            element={
              <RequireAuth>
                <ResourcesPage />
              </RequireAuth>
            }
          />

          <Route
            path="/adaptive/:moduleId"
            element={
              <RequireAuth>
                <AdaptiveQuizPage />
              </RequireAuth>
            }
          />

          <Route
            path="/flashcards/:moduleId"
            element={
              <RequireAuth>
                <FlashcardsPage />
              </RequireAuth>
            }
          />

          <Route
            path="/questions/module/:moduleId"
            element={
              <RequireRole role="teacher">
                <QuestionsPage mode="module" />
              </RequireRole>
            }
          />

          <Route
            path="/questions/resource/:resourceId"
            element={
              <RequireRole role="teacher">
                <QuestionsPage mode="resource" />
              </RequireRole>
            }
          />

          <Route
            path="/review"
            element={
              <RequireRole role="student">
                <ReviewPage />
              </RequireRole>
            }
          />

          {/* Teacher protected */}
          <Route
            path="/t/home"
            element={
              <RequireRole role="teacher">
                <TeacherHomePage />
              </RequireRole>
            }
          />

          <Route
            path="/t/subjects"
            element={
              <RequireRole role="teacher">
                <TeacherSubjectsPage />
              </RequireRole>
            }
          />

          <Route
            path="/t/subject/:subjectId"
            element={
              <RequireRole role="teacher">
                <TeacherSubjectPage />
              </RequireRole>
            }
          />

          <Route
            path="/t/subject/:subjectId/stats"
            element={
              <RequireRole role="teacher">
                <TeacherSubjectStatsPage />
              </RequireRole>
            }
          />

          <Route path="*" element={<div style={{ padding: 24 }}>404</div>} />
      </Routes>

    </Layout>
  );
}
