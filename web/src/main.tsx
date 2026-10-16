import React from "react";
import ReactDOM from "react-dom/client";
import { ConvexProvider, ConvexReactClient } from "convex/react";
import { App } from "./App";
import "./index.css";

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
