import React from "react";
import ReactDOM from "react-dom/client";
import {
  createBrowserRouter,
  Navigate,
  RouterProvider,
} from "react-router-dom";

import "./index.css";

import App from "./App";
import Dashboard from "./pages/Dashboard";
import NewAudit from "./pages/NewAudit";
import AuditResultPage from "./pages/AuditResultPage";

const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: "dashboard",
        element: <Dashboard />,
      },
      {
        path: "audits/new",
        element: <NewAudit />,
      },
      {
        path: "audits/result",
        element: <AuditResultPage />,
      },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/dashboard" replace />,
  },
]);

ReactDOM.createRoot(
  document.getElementById("root")!,
).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
);