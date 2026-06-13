"use client";

import React from 'react';
import { NetworkProvider } from "@/components/providers/NetworkProvider";
import { SimulatorProvider } from "@/components/providers/SimulatorProvider";
import { HmiThemeProvider, useHmiTheme } from "@/components/providers/HmiThemeProvider";
import { GlobalNav } from "@/components/ui/GlobalNav";
import { ClientOnly } from "@/components/ui/ClientOnly";

/** Applies the active HMI theme to the app root so all pages inherit the palette. */
function HmiRoot({ children }: { children: React.ReactNode }) {
    const { theme } = useHmiTheme();
    return (
        <div className="hmi-canvas flex flex-col min-h-screen" data-theme={theme}>
            <GlobalNav />
            <main className="flex-1">{children}</main>
        </div>
    );
}

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
                    <HmiThemeProvider>
                        <HmiRoot>{children}</HmiRoot>
                    </HmiThemeProvider>
                </SimulatorProvider>
            </NetworkProvider>
        </ClientOnly>
    );
}
