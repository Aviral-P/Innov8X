import {
  BarChart3,
  FileSearch,
  LayoutDashboard,
  ShieldCheck,
} from "lucide-react";
import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

interface AppShellProps {
  children: ReactNode;
}

function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-slate-100">
      {/* ================================================== */}
      {/* HEADER */}
      {/* ================================================== */}

      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex h-16 max-w-360 items-center justify-between px-6">
          {/* Brand */}
          <NavLink
            to="/dashboard"
            className="flex items-center gap-3"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-950">
              <ShieldCheck className="h-5 w-5 text-white" />
            </div>

            <div>
              <p className="text-sm font-bold tracking-wide text-slate-950">
                INNOV8X
              </p>

              <p className="text-[11px] text-slate-500">
                Freight Audit Intelligence
              </p>
            </div>
          </NavLink>

          {/* Navigation */}
          <nav className="hidden items-center gap-6 md:flex">
            {/* Dashboard */}
            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                `flex items-center gap-2 text-sm font-medium transition ${
                  isActive
                    ? "text-slate-950"
                    : "text-slate-500 hover:text-slate-900"
                }`
              }
            >
              <LayoutDashboard className="h-4 w-4" />

              Dashboard
            </NavLink>

            {/* New Audit */}
            <NavLink
              to="/audits/new"
              className={({ isActive }) =>
                `flex items-center gap-2 text-sm font-medium transition ${
                  isActive
                    ? "text-slate-950"
                    : "text-slate-500 hover:text-slate-900"
                }`
              }
            >
              <FileSearch className="h-4 w-4" />

              Audits
            </NavLink>

            {/* Analytics - coming later */}
            <span className="flex cursor-not-allowed items-center gap-2 text-sm font-medium text-slate-400">
              <BarChart3 className="h-4 w-4" />

              Analytics

              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                Soon
              </span>
            </span>
          </nav>
        </div>
      </header>

      {/* ================================================== */}
      {/* MAIN CONTENT */}
      {/* ================================================== */}

      <main className="mx-auto max-w-360 px-6 py-8">
        {children}
      </main>
    </div>
  );
}

export default AppShell;