import { memo } from 'react';
import { Play, Pause, Square, RotateCcw, StepForward } from 'lucide-react';
import { ControlButton } from '@/components/ui/ControlButton';
import type { SimulatorStatus } from '@/lib/types';

interface SimulationControlsProps {
    status: SimulatorStatus;
    handleControl: (action: string) => void;
}

export const SimulationControls = memo(({ status, handleControl }: SimulationControlsProps) => (
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
            onClick={() => handleControl('step')}
            variant="indigo"
            icon={StepForward}
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
    </div>
));

SimulationControls.displayName = 'SimulationControls';
