import { AlertTriangle, ShieldAlert, Activity } from 'lucide-react';

interface SecurityAlertProps {
    isUnderAttack: boolean;
    anomalyScore: number;
    compromisedCount: number;
}

export const SecurityAlert = ({ isUnderAttack, anomalyScore, compromisedCount }: SecurityAlertProps) => {
    if (!isUnderAttack && compromisedCount === 0) return null;

    return (
        <div className="absolute top-24 left-1/2 -translate-x-1/2 z-[1100]">
            <div
                className="px-6 py-3 border flex items-center gap-4"
                style={{
                    background: isUnderAttack ? 'var(--alarm-bg)' : 'var(--warn-bg)',
                    borderColor: isUnderAttack ? 'var(--alarm-bd)' : 'var(--warn-bd)',
                }}
            >
                <div>
                    {isUnderAttack ? (
                        <ShieldAlert className="w-5 h-5 text-[var(--alarm)]" />
                    ) : (
                        <AlertTriangle className="w-5 h-5 text-[var(--warn)]" />
                    )}
                </div>

                <div className="flex flex-col">
                    <span
                        className="text-[10px] font-semibold tracking-widest uppercase"
                        style={{ color: isUnderAttack ? 'var(--alarm)' : 'var(--warn)' }}
                    >
                        {isUnderAttack ? 'Cyber Attack Detected' : 'Anomalous Activity'}
                    </span>
                    <div className="flex items-center gap-2">
                        <span className="text-[var(--txt-val)] font-medium text-sm">
                            {compromisedCount} node{compromisedCount !== 1 ? 's' : ''} compromised
                        </span>
                        <div className="w-1 h-1 bg-[var(--line-2)]" />
                        <div className="flex items-center gap-1">
                            <Activity className="w-3 h-3 text-[var(--lbl)]" />
                            <span className="text-[10px] font-medium text-[var(--lbl)] mono">
                                Score: {(anomalyScore * 100).toFixed(1)}%
                            </span>
                        </div>
                    </div>
                </div>

                {isUnderAttack && (
                    <div className="ml-4 px-3 py-1 border border-[var(--alarm-bd)] bg-[var(--alarm-bg)]">
                        <span className="text-[10px] font-semibold text-[var(--alarm)]">VPP SUSPENDED</span>
                    </div>
                )}
            </div>
        </div>
    );
};
