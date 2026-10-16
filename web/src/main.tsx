import React from "react";
import ReactDOM from "react-dom/client";
import { ConvexProvider, ConvexReactClient } from "convex/react";
import { App } from "./App";
import "katex/dist/katex.min.css";
import "./index.css";
import katexMainRegular from "katex/dist/fonts/KaTeX_Main-Regular.woff2?url";
import katexMainBold from "katex/dist/fonts/KaTeX_Main-Bold.woff2?url";
import katexMainItalic from "katex/dist/fonts/KaTeX_Main-Italic.woff2?url";
import katexMathItalic from "katex/dist/fonts/KaTeX_Math-Italic.woff2?url";
import katexAmsRegular from "katex/dist/fonts/KaTeX_AMS-Regular.woff2?url";

for (const href of [
  katexMainRegular,
  katexMainBold,
  katexMainItalic,
  katexMathItalic,
  katexAmsRegular,
]) {
  const link = document.createElement("link");
  link.rel = "preload";
  link.as = "font";
  link.type = "font/woff2";
  link.crossOrigin = "anonymous";
  link.href = href;
  document.head.append(link);
}

interface ViteEnvShape {
  VITE_CONVEX_URL?: string;
}

const metaEnv = (import.meta as unknown as { env?: ViteEnvShape }).env;
const convexUrl = metaEnv?.VITE_CONVEX_URL || "https://valiant-octopus-717.convex.cloud";

const convex = new ConvexReactClient(convexUrl);
const rootElement = document.getElementById("root");

if (rootElement) {
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <ConvexProvider client={convex}>
        <App />
      </ConvexProvider>
    </React.StrictMode>,
  );
}
