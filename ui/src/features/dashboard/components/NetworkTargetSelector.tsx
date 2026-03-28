import React, { useState, useCallback, memo } from 'react';
import { Globe, Settings, ChevronDown, Trash2 } from 'lucide-react';
import { cn } from '../../../utils';

interface NetworkTargetSelectorProps {
    apiTarget: string;
    setApiTarget: (target: string) => void;
    availableTargets: Array<{ label: string; value: string; isCustom?: boolean }>;
    removeTarget: (value: string) => void;
    isConnected: boolean;
}

export const NetworkTargetSelector = memo(({
    apiTarget,
    setApiTarget,
    availableTargets,
    removeTarget,
    isConnected
}: NetworkTargetSelectorProps) => {
    const [showModal, setShowModal] = useState(false);
    const [newTargetUrl, setNewTargetUrl] = useState('');

    const handleAddTarget = useCallback(() => {
        if (newTargetUrl.trim()) {
            setApiTarget(newTargetUrl.trim());
            setNewTargetUrl('');
            setShowModal(false);
        }
    }, [newTargetUrl, setApiTarget]);

    const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleAddTarget();
        }
    }, [handleAddTarget]);

    return (
        <>
            <div className="glass px-5 py-3.5 rounded-2xl flex items-center gap-4 border-indigo-500/10 hover:border-indigo-500/20 transition-all min-w-[200px] lg:min-w-[260px] relative group flex-1">
                <div className="p-2 bg-indigo-500/10 rounded-xl text-indigo-400 group-hover:bg-indigo-500/20 transition-all">
                    <Globe className="w-5 h-5" />
                </div>
                <div className="flex flex-col flex-1 min-w-0 pr-6">
                    <div className="flex items-center justify-between gap-2">
                        <span className="text-[9px] font-black uppercase tracking-widest text-slate-500 leading-none mb-1">Network Target</span>
                        <button
                            onClick={() => setShowModal(true)}
                            className="p-1 hover:bg-white/5 rounded transition-colors -mt-1"
                            aria-label="Network settings"
                        >
                            <Settings className="w-2.5 h-2.5 text-slate-600 hover:text-indigo-400" />
                        </button>
                    </div>
                    <div className="flex items-center gap-2 mt-0.5 relative">
                        <select
                            value={apiTarget}
                            onChange={(e) => {
                                if (e.target.value === 'CUSTOM') {
                                    setShowModal(true);
                                } else {
                                    setApiTarget(e.target.value);
                                }
                            }}
                            className="bg-transparent border-none outline-none text-sm font-black text-white/90 w-full cursor-pointer appearance-none truncate pr-4"
                            aria-label="Select network target"
                        >
                            {availableTargets.map(t => (
                                <option key={t.value} value={t.value} className="bg-slate-900">{t.label}</option>
                            ))}
                            <option value="CUSTOM" className="bg-slate-900">+ Add Custom...</option>
                        </select>
                        <ChevronDown className="w-3 h-3 text-slate-600 absolute right-0 pointer-events-none" />
                    </div>
                </div>
                <div className={cn(
                    "absolute top-3.5 right-3 w-1.5 h-1.5 rounded-full flex-shrink-0 animate-pulse-subtle",
                    isConnected ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" : "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.5)]"
                )} />
            </div>

            {/* Target Modal */}
            {showModal && (
                <div className="fixed inset-0 z-[3000] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4" role="dialog" aria-modal="true">
                    <div className="bg-slate-900 border border-white/10 rounded-2xl w-full max-w-sm p-6 shadow-2xl animate-in zoom-in-95 duration-200">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-lg font-bold text-white">Network Targets</h3>
                            <button onClick={() => setShowModal(false)} className="p-2 hover:bg-white/5 rounded-lg transition-colors" aria-label="Close modal">
                                <ChevronDown className="w-5 h-5 text-slate-400" />
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Saved Environments</label>
                                <div className="space-y-1 max-h-[120px] overflow-y-auto pr-1 custom-scrollbar">
                                    {availableTargets.map(t => (
                                        <div key={t.value} className="flex items-center justify-between p-2 bg-slate-950/50 rounded-lg group">
                                            <div className="flex flex-col">
                                                <span className="text-xs font-bold text-white">{t.label}</span>
                                                <span className="text-[10px] text-slate-500 truncate max-w-[180px]">{t.value || 'Current Origin'}</span>
                                            </div>
                                            {t.isCustom && (
                                                <button
                                                    onClick={() => removeTarget(t.value)}
                                                    className="p-1.5 hover:bg-rose-500/20 rounded-md transition-colors opacity-0 group-hover:opacity-100"
                                                    aria-label={`Remove ${t.label}`}
                                                >
                                                    <Trash2 className="w-3 h-3 text-rose-500" />
                                                </button>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="h-px bg-white/5 my-4" />

                            <div className="space-y-1">
                                <label htmlFor="newTargetUrl" className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Connect to URL</label>
                                <input
                                    id="newTargetUrl"
                                    type="text"
                                    value={newTargetUrl}
                                    onChange={(e) => setNewTargetUrl(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    placeholder="http://localhost:8082"
                                    className="w-full bg-slate-950 border border-white/10 rounded-xl p-3 text-sm text-white outline-none focus:border-indigo-500 transition-colors"
                                    autoFocus
                                />
                            </div>
                            <div className="flex gap-3 pt-2">
                                <button
                                    onClick={() => setShowModal(false)}
                                    className="flex-1 py-3 rounded-xl text-xs font-bold text-slate-400 hover:bg-white/5 transition-colors"
                                >
                                    Close
                                </button>
                                <button
                                    onClick={handleAddTarget}
                                    disabled={!newTargetUrl.trim()}
                                    className="flex-1 py-3 rounded-xl text-xs font-bold bg-indigo-500 text-white hover:bg-indigo-400 transition-all shadow-lg shadow-indigo-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Add & Connect
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
});

NetworkTargetSelector.displayName = 'NetworkTargetSelector';
