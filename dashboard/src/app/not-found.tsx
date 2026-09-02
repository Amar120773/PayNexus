import Link from "next/link";
import { CornerDownLeft, ShieldAlert } from "lucide-react";
import Header from "@/components/Header";

export default function NotFound() {
  return (
    <>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "60vh", padding: "0 32px", textAlign: "center" }} className="animate-fade-in">
        <div style={{ marginBottom: 24, color: "var(--text-disabled)" }}>
          <ShieldAlert size={64} strokeWidth={1.5} />
        </div>
        <div className="font-data" style={{ fontSize: 13, color: "var(--brand-accent)", letterSpacing: "0.1em", marginBottom: 16 }}>
          404 / NOT FOUND
        </div>
        <h1 className="font-poppins-main" style={{ fontSize: "clamp(32px, 5vw, 48px)", color: "var(--text-primary)", marginBottom: 24, lineHeight: 1.1 }}>
          Investigation Not Found
        </h1>
        <p className="font-ui" style={{ fontSize: 16, color: "var(--text-secondary)", maxWidth: 500, margin: "0 auto 48px", lineHeight: 1.6 }}>
          The merchant profile or intelligence report you are looking for does not exist in the active evidence database.
        </p>
        <Link href="/" className="btn btn-primary font-data" style={{ padding: "12px 24px", fontSize: 13, textDecoration: "none", display: "inline-flex", alignItems: "center", gap: 8 }}>
          RETURN TO HUB <CornerDownLeft size={16} />
        </Link>
      </div>
    </>
  );
}
