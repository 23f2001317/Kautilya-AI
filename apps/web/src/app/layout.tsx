// apps/web/src/app/layout.tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Kautilya AI — Autonomous SRE Incident Control Plane",
  description:
    "Enterprise multi-agent autonomous remediation and governance platform.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
