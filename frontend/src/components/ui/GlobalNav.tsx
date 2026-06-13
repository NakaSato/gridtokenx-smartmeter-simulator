"use client";

import { useState, useCallback, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Zap, ChevronDown, Grid3X3, Map as MapIcon, LayoutDashboard, LineChart, Radio, Settings, Trash2 } from 'lucide-react';
import { useNetwork } from '@/components/providers/NetworkProvider';
import { useHmiTheme, type Theme } from '@/components/providers/HmiThemeProvider';
import { cn } from '@/lib/common';

const NAV_ITEMS = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/map', icon: MapIcon, label: 'Grid Map' },
    { to: '/topology', icon: Grid3X3, label: 'Network Graph' },
    { to: '/run', icon: LineChart, label: 'Run Plots' },
];

const THEMES: { value: Theme; label: string }[] = [
    { value: 'dark', label: 'Dark' },
    { value: 'light', label: 'Light' },
    { value: 'contrast', label: 'Hi-Con' },
];

export function GlobalNav() {
    const [open, setOpen] = useState(false);
    const [netOpen, setNetOpen] = useState(false);
    const [netModal, setNetModal] = useState(false);
    const [newTargetUrl, setNewTargetUrl] = useState('');
    const [mounted, setMounted] = useState(false);
    const pathname = usePathname();
    const { apiTarget, setApiTarget, availableTargets, removeTarget } = useNetwork();
    const { theme, setTheme } = useHmiTheme();

    useEffect(() => {
        const frameId = requestAnimationFrame(() => setMounted(true));
        return () => cancelAnimationFrame(frameId);
    }, []);

    const active = NAV_ITEMS.find(i => i.to === pathname);
    const isConnected = mounted && !!apiTarget;

    const handleAddTarget = useCallback(() => {
        if (newTargetUrl.trim()) {
            setApiTarget(newTargetUrl.trim());
            setNewTargetUrl('');
            setNetModal(false);
        }
    }, [newTargetUrl, setApiTarget]);

    return (
        <div className="fixed top-3 right-3 sm:top-5 sm:right-6 md:top-6 md:right-8 z-[9999]">
            <div className="flex items-center gap-1.5 sm:gap-2">
                {/* Theme switcher */}
                <span className="hmi-theme-sw" role="group" aria-label="Theme">
                    {THEMES.map(t => (
                        <button
                            key={t.value}
                            type="button"
                            className={cn('hmi-tsw', theme === t.value && 'active')}
                            onClick={() => setTheme(t.value)}
                        >
                            {t.label}
                        </button>
                    ))}
                </span>

                {/* Page dropdown */}
                <div className="relative">
                    <button
                        type="button"
                        onClick={() => setOpen(!open)}
                        onBlur={() => setTimeout(() => setOpen(false), 200)}
                        className="hmi-btn gap-1.5 sm:gap-2 px-2.5 py-1.5 sm:px-4 sm:py-2"
                    >
                        <Zap className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-[var(--lbl)]" />
                        <span className="hidden sm:inline">{active?.label || 'Page'}</span>
                        <ChevronDown className={cn('w-3 h-3 sm:w-3.5 sm:h-3.5 text-[var(--lbl)] transition-transform', open && 'rotate-180')} />
                    </button>
                    {open && (
                        <div className="absolute top-full right-0 mt-2 w-52 hmi-panel overflow-hidden">
                            <div className="p-1.5">
                                {NAV_ITEMS.map(item => {
                                    const isActive = pathname === item.to;
                                    return (
                                        <Link
                                            key={item.to}
                                            href={item.to}
                                            onClick={() => setOpen(false)}
                                            className={cn(
                                                'flex items-center gap-3 px-3 py-2 text-sm transition-colors',
                                                isActive
                                                    ? 'bg-[var(--panel-2)] text-[var(--txt-val)]'
                                                    : 'text-[var(--txt)] hover:bg-[var(--hover)]'
                                            )}
                                        >
                                            <item.icon className="w-4 h-4 text-[var(--lbl)]" />
                                            {item.label}
                                        </Link>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </div>

                {/* Network target dropdown */}
                <div className="relative">
                    <button
                        type="button"
                        onClick={() => setNetOpen(!netOpen)}
                        onBlur={() => setTimeout(() => setNetOpen(false), 200)}
                        className={cn('hmi-btn gap-1.5 sm:gap-2 px-2 py-1.5 sm:px-3 sm:py-2', netOpen && 'active')}
                    >
                        <span className="relative inline-flex">
                            <Radio className={cn('w-3.5 h-3.5 sm:w-4 sm:h-4', isConnected ? 'text-[var(--ok)]' : 'text-[var(--lbl-dim)]')} />
                            {isConnected && <span className="hmi-dot absolute -top-0.5 -right-0.5 !w-1.5 !h-1.5" />}
                        </span>
                        <span className="truncate max-w-[60px] sm:max-w-[100px] text-[var(--txt)]">
                            {availableTargets.find(t => t.value === apiTarget)?.label || 'Network'}
                        </span>
                        <ChevronDown className={cn('w-3 h-3 sm:w-3.5 sm:h-3.5 text-[var(--lbl)] transition-transform', netOpen && 'rotate-180')} />
                    </button>

                    {netOpen && (
                        <div className="absolute top-full right-0 mt-2 w-72 hmi-panel overflow-hidden">
                            <div className="p-3">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="hmi-lbl">Environments</span>
                                    <button type="button" onClick={() => setNetModal(true)} className="p-1 hover:bg-[var(--hover)] transition-colors">
                                        <Settings className="w-3.5 h-3.5 text-[var(--lbl)]" />
                                    </button>
                                </div>
                                <div className="space-y-1 max-h-[200px] overflow-y-auto">
                                    {availableTargets.map(t => (
                                        <button
                                            type="button"
                                            key={t.value}
                                            onClick={() => { setApiTarget(t.value); setNetOpen(false); }}
                                            className={cn(
                                                'w-full flex items-center justify-between p-2 transition-colors text-left',
                                                apiTarget === t.value
                                                    ? 'bg-[var(--panel-2)] text-[var(--txt-val)]'
                                                    : 'text-[var(--txt)] hover:bg-[var(--hover)]'
                                            )}
                                        >
                                            <div className="flex flex-col min-w-0">
                                                <span className="text-xs font-semibold truncate">{t.label}</span>
                                                <span className="text-[10px] text-[var(--lbl-dim)] truncate max-w-[180px] mono">{t.value || 'Current Origin'}</span>
                                            </div>
                                            {t.isCustom && (
                                                <button
                                                    type="button"
                                                    onClick={(e) => { e.stopPropagation(); removeTarget(t.value); }}
                                                    className="p-1 hover:bg-[var(--alarm-bg)] transition-colors"
                                                >
                                                    <Trash2 className="w-3 h-3 text-[var(--alarm)]" />
                                                </button>
                                            )}
                                        </button>
                                    ))}
                                </div>
                                <button
                                    type="button"
                                    onClick={() => { setNetModal(true); setNetOpen(false); }}
                                    className="hmi-btn w-full mt-2 py-2"
                                >
                                    + Add Custom...
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Network modal */}
            {netModal && (
                <div className="fixed inset-0 z-[99999] flex items-center justify-center bg-black/60 p-4" role="dialog" aria-modal="true">
                    <div className="hmi-panel w-full max-w-sm p-6">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="hmi-title">Network Targets</h3>
                            <button type="button" onClick={() => setNetModal(false)} className="p-2 hover:bg-[var(--hover)] transition-colors">
                                <ChevronDown className="w-5 h-5 text-[var(--lbl)]" />
                            </button>
                        </div>
                        <div className="space-y-4">
                            <div>
                                <label className="hmi-lbl" htmlFor="netTargetUrl">Connect to URL</label>
                                <input
                                    id="netTargetUrl"
                                    type="text"
                                    value={newTargetUrl}
                                    onChange={(e) => setNewTargetUrl(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleAddTarget()}
                                    placeholder="http://localhost:12010"
                                    className="hmi-input w-full mt-1 text-sm mono"
                                    autoFocus
                                />
                            </div>
                            <div className="flex gap-3 pt-2">
                                <button type="button" onClick={() => setNetModal(false)} className="hmi-btn flex-1 py-3">
                                    Close
                                </button>
                                <button
                                    type="button"
                                    onClick={handleAddTarget}
                                    disabled={!newTargetUrl.trim()}
                                    className="hmi-btn primary flex-1 py-3"
                                >
                                    Add &amp; Connect
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
