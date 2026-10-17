import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import App from "./App";
import { AuthProvider } from "./context/AuthContext";
import "@fontsource-variable/manrope";
import "@fontsource-variable/bricolage-grotesque";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
        <Toaster
          position="bottom-right"
          toastOptions={{
            className: "!bg-surface !text-ink !border !border-line !text-sm !rounded-lg",
            success: { iconTheme: { primary: "rgb(var(--good))", secondary: "rgb(var(--surface))" } },
            error: { iconTheme: { primary: "rgb(var(--bad))", secondary: "rgb(var(--surface))" } },
          }}
        />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
