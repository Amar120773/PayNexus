"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { checkHealth } from "@/lib/api";
import { Activity, Sun, Moon } from "lucide-react";

export default function Header() {
  const pathname = usePathname();
  const [apiStatus, setApiStatus] = useState<"checking" | "online" | "offline">("checking");
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    checkHealth()
      .then(() => setApiStatus("online"))
      .catch(() => setApiStatus("offline"));

    const currentTheme = document.documentElement.getAttribute("data-theme") as "light" | "dark" || "light";
    setTheme(currentTheme);
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === "light" ? "dark" : "light";
    setTheme(newTheme);
    localStorage.setItem("theme", newTheme);
    document.documentElement.setAttribute("data-theme", newTheme);
  };

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <header
      style={{
        position: "sticky",
        top: 20,
        zIndex: 50,
        margin: "0 auto 32px",
        width: "calc(100% - 40px)",
        maxWidth: 1200,
      }}
    >
      <div
        className="card"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "16px 24px",
          background: "var(--bg-surface)",
          backdropFilter: "blur(12px)",
          borderRadius: "var(--radius-lg)",
          boxShadow: "var(--shadow-hard)",
        }}
      >
        {/* Left: Brand Identity */}
        <Link href="/" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: 12 }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: "var(--radius-sm)",
              background: "var(--brand)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
              boxShadow: "var(--shadow-hard-accent)",
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--text-inverse)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <span style={{ fontWeight: 800, fontSize: 16, color: "var(--text-primary)", letterSpacing: "-0.02em", lineHeight: 1.1 }}>
              PAYNEXUS
            </span>
            <span className="font-display" style={{ fontSize: 12, color: "var(--text-muted)", fontStyle: "italic", letterSpacing: "0.02em" }}>
              Merchant Risk Intelligence
            </span>
          </div>
        </Link>

        {/* Right: Authenticated Profile & Theme */}
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <button 
            onClick={toggleTheme}
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text-secondary)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: 8,
              borderRadius: "50%",
            }}
            title={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
          >
            {theme === "light" ? <Moon size={18} /> : <Sun size={18} />}
          </button>
          
          <div className="hide-on-mobile" style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", paddingLeft: 8, borderLeft: "1px solid var(--border-subtle)" }}>
            <span className="font-ui" style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)" }}>
              Admin Console
            </span>
            <span className="font-ui" style={{ fontSize: 11, fontWeight: 500, color: "var(--text-muted)" }}>
              Buildathon Demo
            </span>
          </div>
          <div 
            style={{ 
              width: 36, 
              height: 36, 
              borderRadius: "50%", 
              background: "var(--bg-elevated)", 
              border: "1px solid var(--border-default)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--brand-accent)",
              fontWeight: 800,
              fontSize: 14,
              boxShadow: "var(--shadow-xs)"
            }}
          >
            AG
          </div>
        </div>
      </div>
    </header>
  );
}
