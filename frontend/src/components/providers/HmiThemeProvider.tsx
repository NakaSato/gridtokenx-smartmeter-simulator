"use client";

import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';

export type Theme = 'dark' | 'light' | 'contrast';

const STORAGE_KEY = 'gridtokenx_hmi_theme';
const THEMES: Theme[] = ['dark', 'light', 'contrast'];

type ThemeCtx = { theme: Theme; setTheme: (t: Theme) => void };
const HmiThemeContext = createContext<ThemeCtx | null>(null);

/** App-wide HMI theme state. Drives the `data-theme` attribute on the app root,
 *  so every surface (page chrome + scoped `.hmi`/`.hmi-meter`) shares one palette.
 *  Selection persists to localStorage (hot storage) and is restored on mount. */
export function useHmiTheme(): ThemeCtx {
    const ctx = useContext(HmiThemeContext);
    if (!ctx) throw new Error('useHmiTheme must be used inside <HmiThemeProvider>');
    return ctx;
}

export function HmiThemeProvider({ children }: { children: ReactNode }) {
    // Start from the SSR default to avoid a hydration mismatch; restore the saved
    // choice in an effect after mount (localStorage is client-only).
    const [theme, setTheme] = useState<Theme>('dark');

    useEffect(() => {
        try {
            const saved = window.localStorage.getItem(STORAGE_KEY);
            if (saved && (THEMES as string[]).includes(saved)) {
                setTheme(saved as Theme);
            }
        } catch {
            // localStorage unavailable (private mode / SSR) — keep default.
        }
    }, []);

    useEffect(() => {
        try {
            window.localStorage.setItem(STORAGE_KEY, theme);
        } catch {
            // ignore write failures
        }
    }, [theme]);

    return (
        <HmiThemeContext.Provider value={{ theme, setTheme }}>
            {children}
        </HmiThemeContext.Provider>
    );
}
