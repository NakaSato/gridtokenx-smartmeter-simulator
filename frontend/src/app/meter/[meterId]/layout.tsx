import type { Metadata } from "next";
import type { ReactNode } from "react";
import HmiShell from "./HmiShell";

export const metadata: Metadata = {
    title: "Meter Detail · GridTokenX Smart Meter Simulator",
    description: "Per-meter readings, device profile, and energy history.",
};

export default function MeterLayout({ children }: { children: ReactNode }) {
    return <HmiShell>{children}</HmiShell>;
}
