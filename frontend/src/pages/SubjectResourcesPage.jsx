import React from "react";
import { useParams, Navigate } from "react-router-dom";

export default function SubjectResourcesPage() {
  const { subjectId } = useParams();
  return <Navigate to={`/modules/${subjectId}`} replace />;
}
