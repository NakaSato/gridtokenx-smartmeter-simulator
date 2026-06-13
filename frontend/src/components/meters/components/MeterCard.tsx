"use client";

import { memo, useState } from 'react';
import { SlidersHorizontal, Trash2 } from 'lucide-react';

import type { Reading } from '@/lib/types';
import { cn } from '@/lib/common';
import { deriveMeter } from './meterHmi';
import './MeterHmi.css';

interface MeterCardProps {
    reading: Reading;
    onClick?: () => void;
    onEdit?: (reading: Reading) => void;
    onMeta?: (reading: Reading) => void;
    onDelete?: (meter_id: string) => void;
    compact?: boolean;
}

export const MeterCard = memo(({ reading, onClick, onEdit, onMeta, onDelete, compact = false }: MeterCardProps) => {
    const [copied, setCopied] = useState(false);
    const m = deriveMeter(reading);

    const handleCopySerial = async (e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            await navigator.clipboard.writeText(reading.serial_number || reading.meter_id);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    const handleDelete = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (onDelete && confirm(`Delete meter ${reading.meter_id}?`)) onDelete(reading.meter_id);
    };

    return (
        <div
            className={cn('hmi-meter', m.abnormal && 'abn')}
            data-view={compact ? 'list' : undefined}
            onClick={onClick}
        >
            {/* Header */}
            <div className="hd">
                <button
                    type="button"
                    className={cn('id', copied && 'copied')}
                    onClick={handleCopySerial}
                    title="Click to copy ID"
                >
                    {m.id}
                </button>
                <span className="hd-r">
                    <span className="acts">
                        {onEdit && (
                            <button type="button" className="act" onClick={(e) => { e.stopPropagation(); onEdit(reading); }}>
                                Config
                            </button>
                        )}
                        {onMeta && (
                            <button type="button" className="act" title="Edit metadata profile" onClick={(e) => { e.stopPropagation(); onMeta(reading); }}>
                                <SlidersHorizontal className="w-3 h-3" />
                            </button>
                        )}
                        {onDelete && (
                            <button type="button" className="act danger" title="Delete meter" onClick={handleDelete}>
                                <Trash2 className="w-3 h-3" />
                            </button>
                        )}
                    </span>
                    <span className={cn('tag', m.isSolar ? 'solar' : 'grid')}>{m.typeLabel}</span>
                </span>
            </div>

            <div className="bd">
                {/* Power + net-flow */}
                <div>
                    <div className="pwr">
                        <div className="blk">
                            <div className="k">Generation</div>
                            <div className="n mono">{m.gen.toFixed(2)}<span className="u">kW</span></div>
                        </div>
                        <div className="role">
                            <div>
                                <span className={cn('badge', m.isExport ? 'exp' : 'imp')}>{m.isExport ? 'Export' : 'Import'}</span>
                            </div>
                            <div className="sub">{m.roleSub}</div>
                        </div>
                        <div className="blk r">
                            <div className="k">Consumption</div>
                            <div className="n mono">{m.con.toFixed(2)}<span className="u">kW</span></div>
                        </div>
                    </div>

                    <div className="nf">
                        <div className="zero" />
                        <div
                            className={cn('fill', m.isExport ? 'exp' : 'imp')}
                            style={{ width: `${m.barPct}%` }}
                        />
                    </div>
                    <div className="nf-scale">
                        <span>−{m.barScale} import</span>
                        <span>net {m.net >= 0 ? '+' : ''}{m.net} kW</span>
                        <span>+{m.barScale} export</span>
                    </div>

                    <div className="sec2">
                        <div className="c">
                            <div className="k">Energy storage</div>
                            <div className="v mono">{m.soc.toFixed(0)}<span className="u">%</span></div>
                        </div>
                        <div className="c">
                            <div className="k">Carbon offset</div>
                            <div className="v mono">{m.co2.toFixed(1)}<span className="u">kg</span></div>
                        </div>
                    </div>
                </div>

                {/* Electrical + footer */}
                <div>
                    <div className="elec">
                        <div className={cn('c', m.fv && 'flag', m.fv === 'alarm' && 'al')}>
                            <div className="k">Voltage</div>
                            <div className={cn('v mono', m.fv)}>{m.v.toFixed(3)}<span className="u">pu</span></div>
                        </div>
                        <div className={cn('c', m.ff && 'flag', m.ff === 'alarm' && 'al')}>
                            <div className="k">Frequency</div>
                            <div className={cn('v mono', m.ff)}>{m.f.toFixed(2)}<span className="u">Hz</span></div>
                        </div>
                        <div className={cn('c', m.fp && 'flag', m.fp === 'alarm' && 'al')}>
                            <div className="k">Power factor</div>
                            <div className={cn('v mono', m.fp)}>{m.pf.toFixed(2)}<span className="u">cosφ</span></div>
                        </div>
                    </div>

                    <div className="foot">
                        <div className="fi">
                            <div className="k">Ambient</div>
                            <div className="v mono">{m.amb.toFixed(1)}°C</div>
                        </div>
                        <div className="fi">
                            <div className="k">Network</div>
                            <div className="v live"><span className={cn('dot', !m.live && 'stale')} />{m.live ? 'Live' : 'Stale'}</div>
                        </div>
                        <span className="spacer" />
                        {m.abnormal && <span className="abn-tag">Check</span>}
                    </div>
                </div>
            </div>
        </div>
    );
});

MeterCard.displayName = 'MeterCard';
