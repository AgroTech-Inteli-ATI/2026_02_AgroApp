import React from "react";
import ReactDOM from "react-dom/client";
import "@fontsource/poppins/latin-400.css";
import "@fontsource/poppins/latin-500.css";
import "@fontsource/poppins/latin-600.css";
import "@fontsource/poppins/latin-700.css";
import App from "./App";
import "./global.css";

// Só no build: no dev o Vite serve módulos sem hash e o cache ficaria desatualizado.
if (import.meta.env.PROD && "serviceWorker" in navigator)
  void navigator.serviceWorker
    .register(`${import.meta.env.BASE_URL}sw.js`)
    .catch((error) => console.error("Falha ao registrar o modo offline:", error));

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
