import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { NetworkProvider } from "@/components/providers/NetworkProvider";
import { SimulatorProvider } from "@/components/providers/SimulatorProvider";
import { GlobalNav } from "@/components/ui/GlobalNav";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "GridTokenX Smart Meter Simulator",
  description: "AMI and Grid Orchestration Simulator for P2P Energy Trading",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-slate-950 text-slate-100`}
      >
        <NetworkProvider>
          <SimulatorProvider>
            <GlobalNav />
            {children}
          </SimulatorProvider>
        </NetworkProvider>
      </body>
    </html>
  );
}
