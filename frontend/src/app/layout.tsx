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
import { Geist } from "next/font/google";
import { cn } from "@/lib/utils";

const geist = Geist({subsets:['latin'],variable:'--font-sans'});


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={cn("dark", "font-sans", geist.variable)}>
      <body className="antialiased hmi-canvas">
        <AppProvider>{children}</AppProvider>
      </body>
    </html>
  );
}
