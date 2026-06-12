import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
    title: "Run Plots · GridTokenX Smart Meter Simulator",
    description: "Time-series plots of a deterministic simulation run from InfluxDB.",
};

export default function RunLayout({ children }: { children: ReactNode }) {
    return children;
}
