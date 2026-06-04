import type { Metadata } from "next";
import "./globals.css";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "GridTokenX Smart Meter Simulator",
  description: "AMI and Grid Orchestration Simulator for P2P Energy Trading",
  icons: {
    icon: "/favicon.ico",
  },
};

import { AppProvider } from "@/components/providers/AppProvider";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased bg-slate-950 text-slate-100">
        <AppProvider>{children}</AppProvider>
      </body>
    </html>
  );
}
