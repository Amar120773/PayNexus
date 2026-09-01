import type { Metadata } from "next";
import { Inter, Newsreader, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Header from "@/components/Header";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const newsreader = Newsreader({ subsets: ["latin"], variable: "--font-newsreader", style: ["normal", "italic"] });
const jetbrains = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains" });

export const metadata: Metadata = {
  title: "PayNexus | Merchant Risk Intelligence",
  description: "Investigator console for merchant mule risk assessment powered by the MuleHunter detection engine",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${newsreader.variable} ${jetbrains.variable}`}>
      <body
        style={{
          display: "flex",
          flexDirection: "column",
          minHeight: "100vh",
          background: "var(--bg-page)",
          color: "var(--text-primary)",
        }}
      >
        <Header />

        <main style={{ flex: 1, display: "flex", flexDirection: "column", maxWidth: "100%", overflowX: "hidden" }}>
          {children}
        </main>
      </body>
    </html>
  );
}
