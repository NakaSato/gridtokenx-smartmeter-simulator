"use client";

import React from 'react';
import { NetworkProvider } from "@/components/providers/NetworkProvider";
import { SimulatorProvider } from "@/components/providers/SimulatorProvider";
import { GlobalNav } from "@/components/ui/GlobalNav";
import { ClientOnly } from "@/components/ui/ClientOnly";

/**
 * A unified provider component for all client-side contexts.
 * This should be used at a level where it only renders in the browser,
 * or wrapped in a ClientOnly boundary.
 */
export function AppProvider({ children }: { children: React.ReactNode }) {
    return (
        <ClientOnly>
            <NetworkProvider>
                <SimulatorProvider>
                    <div className="flex flex-col min-h-screen">
                        <GlobalNav />
                        <main className="flex-1">
                            {children}
                        </main>
                    </div>
                </SimulatorProvider>
            </NetworkProvider>
        </ClientOnly>
    );
}
