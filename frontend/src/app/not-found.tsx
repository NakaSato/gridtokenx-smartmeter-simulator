"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { ClientOnly } from "@/components/ui/ClientOnly";

export default function NotFound() {
  return (
    <ClientOnly>
      <div className="min-h-screen bg-[var(--canvas)] flex items-center justify-center p-4">
        <div className="hmi-panel p-8 text-center max-w-md">
          <h1 className="text-6xl font-semibold text-[var(--txt-val)] mb-2 mono">404</h1>
          <p className="text-sm text-[var(--lbl)] mb-8 hmi-lbl">Page not found</p>
          <Link href="/dashboard" className="hmi-btn primary inline-flex">
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>
        </div>
      </div>
    </ClientOnly>
  );
}
