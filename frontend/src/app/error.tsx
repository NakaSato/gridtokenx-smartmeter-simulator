"use client";

import { useEffect } from 'react';
import Link from 'next/link';
import { Zap, Home, AlertTriangle, ArrowLeft } from 'lucide-react';

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
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="text-center max-w-md">
        <div className="flex items-center justify-center gap-2 mb-6">
          <AlertTriangle className="w-12 h-12 text-rose-400" />
        </div>
        <h1 className="text-4xl font-black text-white mb-2">Something went wrong</h1>
        <p className="text-slate-400 mb-6">{error.message || 'An unexpected error occurred'}</p>
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={reset}
            className="px-6 py-3 bg-emerald-500/20 text-emerald-400 rounded-xl font-bold text-sm hover:bg-emerald-500/30 transition-colors"
          >
            Try Again
          </button>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 px-6 py-3 bg-slate-800 text-slate-300 rounded-xl font-bold text-sm hover:bg-slate-700 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
