"use client";

import { useEffect } from 'react';
import Link from 'next/link';
import { AlertTriangle, ArrowLeft } from 'lucide-react';

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Application error:', error);
  }, [error]);

  return (
    <div className="min-h-screen bg-[var(--canvas)] flex items-center justify-center p-4">
      <div className="hmi-panel p-8 text-center max-w-md">
        <div className="flex items-center justify-center mb-6">
          <AlertTriangle className="w-12 h-12 text-[var(--alarm)]" />
        </div>
        <h1 className="text-2xl font-semibold text-[var(--txt-val)] mb-2">Something went wrong</h1>
        <p className="text-sm text-[var(--lbl)] mb-6">{error.message || 'An unexpected error occurred'}</p>
        <div className="flex items-center justify-center gap-3">
          <button type="button" onClick={reset} className="hmi-btn primary">
            Try Again
          </button>
          <Link href="/dashboard" className="hmi-btn inline-flex">
            <ArrowLeft className="w-4 h-4" />
            Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
