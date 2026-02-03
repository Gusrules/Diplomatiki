import React from "react";

export default function InfoBox({ title = "Info", children }) {
  return (
    <div className="infobox">
      <div className="infobox-title">{title}</div>
      <div className="infobox-body">{children}</div>
    </div>
  );
}
