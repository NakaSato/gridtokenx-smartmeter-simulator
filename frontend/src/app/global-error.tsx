"use client";

import type { CSSProperties } from "react";

// global-error replaces the root layout entirely, so app CSS (globals.css) is
// not loaded here — styles must be inline. Hoisting the objects to module scope
// keeps a stable reference across renders instead of rebuilding each render.
const bodyStyle: CSSProperties = { margin: 0, background: "#1f2225", color: "#cfd3d7", fontFamily: "system-ui, sans-serif" };
const overlayStyle: CSSProperties = { minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: 16 };
const panelStyle: CSSProperties = { background: "#25292d", border: "1px solid #3a3f44", padding: 24, maxWidth: 420, textAlign: "center" };
const titleStyle: CSSProperties = { margin: "0 0 8px", fontSize: 18, fontWeight: 600, color: "#e6e9ec" };
const messageStyle: CSSProperties = { margin: "0 0 16px", fontSize: 13, color: "#868d95" };
const buttonStyle: CSSProperties = {
  fontSize: 12,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
  color: "#e6e9ec",
  background: "#2a2e32",
  border: "1px solid #5f93c0",
  padding: "7px 14px",
  cursor: "pointer",
};

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body style={bodyStyle}>
        <div style={overlayStyle}>
          <div style={panelStyle}>
            <h2 style={titleStyle}>Something went wrong!</h2>
            <p style={messageStyle}>{error.message || "An unexpected error occurred"}</p>
            <button
              type="button"
              onClick={() => reset()}
              style={buttonStyle}
            >
              Try again
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
