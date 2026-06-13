import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
    title: "Grid Map · GridTokenX Smart Meter Simulator",
    description: "Geospatial view of smart meters, feeders, and live grid telemetry.",
};

export default function MapLayout({ children }: { children: ReactNode }) {
    return children;
}
