import React from "react";

export default function Toast({ message, onClose }) {
  if (!message) return null;
  return (
    <div
      style={{
        position: "fixed",
        right: 16,
        bottom: 16,
        background: "#111",
        color: "#fff",
        padding: "12px 14px",
        borderRadius: 10,
        maxWidth: 360,
      }}
      onClick={onClose}
      title="click to close"
    >
      {message}
    </div>
  );
}
