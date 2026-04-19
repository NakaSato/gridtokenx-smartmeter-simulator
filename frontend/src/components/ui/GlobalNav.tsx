"use client";

import { useState, useCallback } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Zap, ChevronDown, Box, Map as MapIcon, Activity, Globe, Grid, MapPin, LayoutDashboard, Radio, Settings, Trash2 } from 'lucide-react';
import { useNetwork } from '@/components/providers/NetworkProvider';
import { cn } from '@/lib/common';

const NAV_ITEMS = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/vpp', icon: Box, label: 'VPP Ops' },
    { to: '/adr', icon: Activity, label: 'ADR' },
    { to: '/map', icon: MapIcon, label: 'Grid Map' },
    { to: '/topology', icon: Zap, label: 'Topology 3D' },
    { to: '/lpc', icon: Globe, label: 'LPC' },
    { to: '/resilience', icon: Activity, label: 'Resilience' },
];

export function GlobalNav() {
    const [open, setOpen] = useState(false);
    const [netOpen, setNetOpen] = useState(false);
    const [netModal, setNetModal] = useState(false);
    const [newTargetUrl, setNewTargetUrl] = useState('');
    const pathname = usePathname();
    const { apiTarget, setApiTarget, availableTargets, removeTarget } = useNetwork();

    const active = NAV_ITEMS.find(i => i.to === pathname);
    const isConnected = !!apiTarget;

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
                {/* Page dropdown */}
                <div className="relative">
                    <button
                        onClick={() => setOpen(!open)}
                        onBlur={() => setTimeout(() => setOpen(false), 200)}
                        className="flex items-center gap-1.5 sm:gap-2 px-2.5 py-1.5 sm:px-4 sm:py-2 bg-slate-900/90 backdrop-blur-xl border border-white/10 rounded-lg sm:rounded-xl text-white shadow-2xl hover:border-emerald-500/40 transition-all cursor-pointer"
                    >
                        <Zap className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-emerald-400" />
                        <span className="font-bold text-[10px] sm:text-sm hidden sm:inline">{active?.label || 'Page'}</span>
                        <ChevronDown className={`w-3 h-3 sm:w-3.5 sm:h-3.5 text-slate-400 transition-transform ${open ? 'rotate-180' : ''}`} />
                    </button>
                    {open && (
                        <div className="absolute top-full right-0 mt-2 w-52 bg-slate-900/95 backdrop-blur-xl border border-white/10 rounded-xl shadow-2xl overflow-hidden">
                            <div className="p-1.5">
                                {NAV_ITEMS.map(item => {
                                    const isActive = pathname === item.to;
                                    return (
                                        <Link
                                            key={item.to}
                                            href={item.to}
                                            onClick={() => setOpen(false)}
                                            className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                                                isActive
                                                    ? 'bg-emerald-500/15 text-emerald-400'
                                                    : 'text-slate-300 hover:bg-white/5 hover:text-white'
                                            }`}
                                        >
                                            <item.icon className="w-4 h-4" />
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
                        onClick={() => setNetOpen(!netOpen)}
                        onBlur={() => setTimeout(() => setNetOpen(false), 200)}
                        className={cn(
                            'flex items-center gap-1.5 sm:gap-2 px-2 py-1.5 sm:px-3 sm:py-2 bg-slate-900/90 backdrop-blur-xl border rounded-lg sm:rounded-xl shadow-2xl transition-all cursor-pointer',
                            netOpen ? 'border-indigo-500/40' : 'border-white/10 hover:border-indigo-500/20'
                        )}
                    >
                        <div className="relative">
                            <Radio className={cn('w-3.5 h-3.5 sm:w-4 sm:h-4 transition-colors', isConnected ? 'text-emerald-400' : 'text-slate-500')} />
                            {isConnected && <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />}
                        </div>
                        <span className="text-[10px] sm:text-xs font-medium text-white/80 truncate max-w-[60px] sm:max-w-[100px]">
                            {availableTargets.find(t => t.value === apiTarget)?.label || 'Network'}
                        </span>
                        <ChevronDown className={`w-3 h-3 sm:w-3.5 sm:h-3.5 text-slate-400 transition-transform ${netOpen ? 'rotate-180' : ''}`} />
                    </button>

                    {netOpen && (
                        <div className="absolute top-full right-0 mt-2 w-72 bg-slate-900/95 backdrop-blur-xl border border-white/10 rounded-xl shadow-2xl overflow-hidden">
                            <div className="p-3">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-[9px] font-black uppercase tracking-widest text-slate-500">Environments</span>
                                    <button onClick={() => setNetModal(true)} className="p-1 hover:bg-white/5 rounded transition-colors">
                                        <Settings className="w-3.5 h-3.5 text-slate-500 hover:text-indigo-400" />
                                    </button>
                                </div>
                                <div className="space-y-1 max-h-[200px] overflow-y-auto">
                                    {availableTargets.map(t => (
                                        <button
                                            key={t.value}
                                            onClick={() => { setApiTarget(t.value); setNetOpen(false); }}
                                            className={`w-full flex items-center justify-between p-2 rounded-lg transition-colors text-left ${
                                                apiTarget === t.value
                                                    ? 'bg-emerald-500/15 text-emerald-400'
                                                    : 'text-slate-300 hover:bg-white/5'
                                            }`}
                                        >
                                            <div className="flex flex-col min-w-0">
                                                <span className="text-xs font-bold truncate">{t.label}</span>
                                                <span className="text-[10px] text-slate-500 truncate max-w-[180px]">{t.value || 'Current Origin'}</span>
                                            </div>
                                            {t.isCustom && (
                                                <button
                                                    onClick={(e) => { e.stopPropagation(); removeTarget(t.value); }}
                                                    className="p-1 hover:bg-rose-500/20 rounded transition-colors"
                                                >
                                                    <Trash2 className="w-3 h-3 text-rose-500" />
                                                </button>
                                            )}
                                        </button>
                                    ))}
                                </div>
                                <button
                                    onClick={() => { setNetModal(true); setNetOpen(false); }}
                                    className="w-full mt-2 py-2 text-xs font-bold text-indigo-400 hover:bg-indigo-500/10 rounded-lg transition-colors"
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
                <div className="fixed inset-0 z-[99999] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4" role="dialog" aria-modal="true">
                    <div className="bg-slate-900 border border-white/10 rounded-2xl w-full max-w-sm p-6 shadow-2xl">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-lg font-bold text-white">Network Targets</h3>
                            <button onClick={() => setNetModal(false)} className="p-2 hover:bg-white/5 rounded-lg transition-colors">
                                <ChevronDown className="w-5 h-5 text-slate-400" />
                            </button>
                        </div>
                        <div className="space-y-4">
                            <div>
                                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Connect to URL</label>
                                <input
                                    type="text"
                                    value={newTargetUrl}
                                    onChange={(e) => setNewTargetUrl(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleAddTarget()}
                                    placeholder="http://localhost:8082"
                                    className="w-full mt-1 bg-slate-950 border border-white/10 rounded-xl p-3 text-sm text-white outline-none focus:border-indigo-500 transition-colors"
                                    autoFocus
                                />
                            </div>
                            <div className="flex gap-3 pt-2">
                                <button onClick={() => setNetModal(false)} className="flex-1 py-3 rounded-xl text-xs font-bold text-slate-400 hover:bg-white/5 transition-colors">
                                    Close
                                </button>
                                <button
                                    onClick={handleAddTarget}
                                    disabled={!newTargetUrl.trim()}
                                    className="flex-1 py-3 rounded-xl text-xs font-bold bg-indigo-500 text-white hover:bg-indigo-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Add & Connect
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
