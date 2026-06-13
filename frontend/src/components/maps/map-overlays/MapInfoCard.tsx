import { Clock, Shield } from 'lucide-react';

interface MapInfoCardProps {
    metersCount: number;
    healthScore?: number;
    carbonSaved?: number;
    anomalyCount?: number;
}

export const MapInfoCard = ({
    metersCount,
    healthScore = 100,
    carbonSaved = 0,
    anomalyCount = 0
}: MapInfoCardProps) => {
    return (
        <div className="absolute top-20 right-4 sm:top-24 sm:right-6 z-[1000] glass px-3 sm:px-4 py-2 sm:py-3 max-w-[200px] sm:max-w-xs">
            <div className="flex items-start">
                <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                        <h4 className="text-sm font-semibold text-[var(--txt-val)]">Village Microgrid</h4>
                        <div
                            className={`hmi-bdg ${healthScore > 90 ? 'ok' : 'alarm'}`}
                        >
                            <span className="mono">{healthScore.toFixed(0)}%</span> HEALTH
                        </div>
                    </div>
                    <p className="text-xs text-[var(--lbl)] leading-relaxed mb-4">
                        Real-time monitoring of {metersCount} smart meters with solar generation and VPP coordination.
                    </p>

                    <div className="grid grid-cols-2 gap-3 mb-4">
                        <div className="flex flex-col">
                            <span className="hmi-lbl">CO2 Saved</span>
                            <span className="text-xs font-medium text-[var(--txt-val)] mono">{(carbonSaved / 1000).toFixed(2)} kg</span>
                        </div>
                        <div className="flex flex-col">
                            <span className="hmi-lbl">Anomalies</span>
                            <span className="text-xs font-medium mono" style={{ color: anomalyCount > 0 ? 'var(--alarm)' : 'var(--txt)' }}>
                                {anomalyCount} detected
                            </span>
                        </div>
                    </div>

                    <div className="flex items-center gap-3 pt-3 border-t border-[var(--line)]">
                        <div className="flex items-center gap-1.5">
                            <Clock className="w-3.5 h-3.5 text-[var(--lbl)]" />
                            <span className="text-[10px] font-medium text-[var(--lbl)]">Real-time</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <Shield className="w-3.5 h-3.5 text-[var(--lbl)]" />
                            <span className="text-[10px] font-medium text-[var(--lbl)]">Signed</span>
                        </div>
                        <div className="flex-1" />
                        <span className="hmi-chip">AMI Enabled</span>
                    </div>
                </div>
            </div>
        </div>
    );
};
