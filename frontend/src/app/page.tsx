import type { Metadata } from "next";
import { redirect } from "next/navigation";

export const metadata: Metadata = {
  title: "GridTokenX Smart Meter Simulator",
  description: "AMI and grid orchestration simulator for P2P energy trading.",
};

export default function Home() {
  redirect("/dashboard");
}
