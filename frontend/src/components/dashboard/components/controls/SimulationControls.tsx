import { memo } from 'react';
import { Play, Pause, Square, RotateCcw, Box } from 'lucide-react';
import { ControlButton } from '@/components/ui/ControlButton';
import type { SimulatorStatus } from '@/lib/types';

interface SimulationControlsProps {
    status: SimulatorStatus;
    handleControl: (action: string) => void;
    onUpdateScenario?: (scenario: string) => Promise<void>;
}

export const SimulationControls = memo(({ status, handleControl, onUpdateScenario }: SimulationControlsProps) => (
    <div className="flex items-center gap-3">
        <ControlButton
            onClick={() => handleControl('start')}
            disabled={status.running}
            variant="emerald"
            icon={Play}
        />
        <ControlButton
            onClick={() => handleControl('pause')}
            disabled={!status.running || status.paused}
            variant="amber"
            icon={Pause}
        />
        <ControlButton
            onClick={() => handleControl('resume')}
            disabled={!status.paused}
            variant="blue"
            icon={Play}
        />
        <ControlButton
            onClick={() => handleControl('stop')}
            disabled={!status.running}
            variant="rose"
            icon={Square}
        />
        <ControlButton
            onClick={() => handleControl('restart')}
            variant="indigo"
            icon={RotateCcw}
        />
        <div className="flex items-center gap-1 bg-slate-900/50 px-3 py-2 rounded-xl ml-2 shadow-inner">
            <Box className="w-3 h-3 text-slate-500" />
            <select
                id="scenarioSelect"
                defaultValue=""
                onChange={(e) => onUpdateScenario?.(e.target.value)}
                className="bg-transparent text-[10px] font-black text-slate-400 outline-none uppercase cursor-pointer"
            >
                <option value="" disabled>Scenario</option>
                <option value="ieee123">IEEE 123-Node</option>
                <option value="ieee8500">IEEE 8500-Node</option>
            </select>
        </div>
    </div>
));

SimulationControls.displayName = 'SimulationControls';
