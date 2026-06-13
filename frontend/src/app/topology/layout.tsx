import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
    title: "Grid Topology · GridTokenX Smart Meter Simulator",
    description: "Interactive feeder topology graph — buses, lines, and meter mapping.",
};

export default function TopologyLayout({ children }: { children: ReactNode }) {
    return children;
}
