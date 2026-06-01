"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Play, 
  Square, 
  Settings, 
  Activity, 
  Info, 
  RefreshCw,
  Power,
  CheckCircle2,
  AlertTriangle,
  Network
} from 'lucide-react';
import { useNetwork } from '@/components/providers/NetworkProvider';
import { useSimulator } from '@/components/providers/SimulatorProvider';

interface LoadShedStatus {
  is_active: boolean;
  scenario_loaded: boolean;
  steps_count: number;
  executed_steps: number[];
  shedded_meters: string[];
  elapsed_seconds: number;
  latency_enabled?: boolean;
  latency_per_hop_seconds?: number;
}

export function LoadShedControl() {
  const { getApiUrl } = useNetwork();
  const { readings, status } = useSimulator();

  const [scenarioStatus, setScenarioStatus] = useState<LoadShedStatus>({
    is_active: false,
    scenario_loaded: false,
    steps_count: 0,
    executed_steps: [],
    shedded_meters: [],
    elapsed_seconds: 0,
    latency_enabled: false,
    latency_per_hop_seconds: 1.0
  });
  const [loading, setLoading] = useState(false);

  // Local settings before loading
  const [latencyEnabled, setLatencyEnabled] = useState(false);
  const [latencyPerHop, setLatencyPerHop] = useState(1.0);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(getApiUrl('/api/v1/simulation/scenarios/loadshed/status'));
      if (res.ok) {
        const data = await res.json();
        setScenarioStatus(data);
        if (data.scenario_loaded) {
          setLatencyEnabled(data.latency_enabled || false);
          setLatencyPerHop(data.latency_per_hop_seconds || 1.0);
        }
      }
    } catch (e) {
      console.error('Error fetching load shed status:', e);
    }
  }, [getApiUrl]);

  // Poll status while simulation is running
  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, status.running ? 2000 : 5000);
    return () => clearInterval(interval);
  }, [fetchStatus, status.running]);

  // Dynamically generate and load a scenario using active meter IDs
  const handleLoadMockScenario = async () => {
    if (readings.length === 0) return;
    setLoading(true);
    
    // Pick the first two active meter IDs
    const meter1 = readings[0]?.meter_id;
    const meter2 = readings[1]?.meter_id || readings[0]?.meter_id;

    // Build scenario: shed meter1 at 10s, shed meter2 at 20s, restore both at 35s
    const mockPayload = {
      scenario: {
        "5": {
          [meter1]: "OUT_OF_SERVICE"
        },
        "15": {
          [meter2]: "OUT_OF_SERVICE"
        },
        "25": {
          [meter1]: "IN_SERVICE",
          [meter2]: "IN_SERVICE"
        }
      },
      latency_enabled: latencyEnabled,
      latency_per_hop_seconds: latencyPerHop
    };

    try {
      const res = await fetch(getApiUrl('/api/v1/simulation/scenarios/loadshed/load'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockPayload)
      });
      if (res.ok) {
        await fetchStatus();
      }
    } catch (e) {
      console.error('Failed to load scenario:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleStartScenario = async () => {
    setLoading(true);
    try {
      const res = await fetch(getApiUrl('/api/v1/simulation/scenarios/loadshed/start'), {
        method: 'POST'
      });
      if (res.ok) {
        await fetchStatus();
      }
    } catch (e) {
      console.error('Failed to start scenario:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleStopScenario = async () => {
    setLoading(true);
    try {
      const res = await fetch(getApiUrl('/api/v1/simulation/scenarios/loadshed/stop'), {
        method: 'POST'
      });
      if (res.ok) {
        await fetchStatus();
      }
    } catch (e) {
      console.error('Failed to stop scenario:', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass rounded-3xl p-6 border border-white/10 space-y-4 shadow-2xl">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-black uppercase tracking-widest text-slate-400 flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-400" /> Time-Series Load Shed
        </h2>
        {scenarioStatus.is_active ? (
          <span className="text-[10px] font-black text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-full border border-rose-500/20 animate-pulse">
            Active: {scenarioStatus.elapsed_seconds}s
          </span>
        ) : (
          <span className="text-[10px] font-black text-slate-500 bg-slate-900/50 px-2 py-0.5 rounded-full border border-white/5">
            Idle
          </span>
        )}
      </div>

      <div className="space-y-3">
        {/* Scenario Info */}
        <div className="bg-slate-950/40 p-4 rounded-2xl border border-white/5 space-y-2 text-xs">
          <div className="flex justify-between items-center text-slate-400">
            <span>Scenario Configuration</span>
            <span className="font-bold text-slate-200">
              {scenarioStatus.scenario_loaded ? "Loaded" : "No file"}
            </span>
          </div>
          {scenarioStatus.scenario_loaded && (
            <div className="grid grid-cols-2 gap-2 pt-1.5 border-t border-white/5 text-[11px] text-slate-400">
              <div>
                Steps: <span className="font-bold text-slate-200">{scenarioStatus.steps_count}</span>
              </div>
              <div>
                Executed: <span className="font-bold text-slate-200">{scenarioStatus.executed_steps.length}</span>
              </div>
              <div className="col-span-2 pt-1.5 border-t border-white/5 flex justify-between">
                <span>P2P Cyber Latency:</span>
                <span className="font-bold text-indigo-400">
                  {scenarioStatus.latency_enabled 
                    ? `Enabled (${scenarioStatus.latency_per_hop_seconds}s/hop)` 
                    : "Disabled"}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Latency Settings Toggles */}
        {!scenarioStatus.is_active && (
          <div className="bg-slate-950/40 p-4 rounded-2xl border border-white/5 space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px] flex items-center gap-1.5">
                <Network className="w-3.5 h-3.5 text-indigo-400" /> Mode Cyber Latency (ns-3)
              </span>
              <input
                type="checkbox"
                checked={latencyEnabled}
                onChange={(e) => setLatencyEnabled(e.target.checked)}
                disabled={loading || scenarioStatus.scenario_loaded}
                className="w-4 h-4 accent-indigo-500 bg-slate-800 border-slate-700 rounded cursor-pointer disabled:opacity-50"
              />
            </div>
            {latencyEnabled && (
              <div className="space-y-1.5 pt-1.5 border-t border-white/5">
                <div className="flex justify-between text-[10px] text-slate-400">
                  <span>Propagation Delay / Hop</span>
                  <span className="font-bold text-indigo-400">{latencyPerHop.toFixed(1)}s</span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="5.0"
                  step="0.5"
                  value={latencyPerHop}
                  onChange={(e) => setLatencyPerHop(parseFloat(e.target.value))}
                  disabled={loading || scenarioStatus.scenario_loaded}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500 disabled:opacity-50"
                />
              </div>
            )}
          </div>
        )}

        {/* Action Controls */}
        <div className="flex gap-2">
          {!scenarioStatus.scenario_loaded ? (
            <button
              onClick={handleLoadMockScenario}
              disabled={loading || readings.length === 0}
              className="w-full py-2.5 rounded-xl text-xs font-black uppercase tracking-wider bg-indigo-500 hover:bg-indigo-400 text-white transition-all disabled:opacity-50 cursor-pointer flex items-center justify-center gap-1.5 active:scale-95"
            >
              <Settings className="w-3.5 h-3.5" /> Configure Mock
            </button>
          ) : !scenarioStatus.is_active ? (
            <div className="flex gap-2 w-full">
              <button
                onClick={handleStartScenario}
                disabled={loading}
                className="flex-1 py-2.5 rounded-xl text-xs font-black uppercase tracking-wider bg-emerald-500 hover:bg-emerald-400 text-white transition-all disabled:opacity-50 cursor-pointer flex items-center justify-center gap-1.5 active:scale-95"
              >
                <Play className="w-3.5 h-3.5" /> Start Runner
              </button>
              <button
                onClick={handleLoadMockScenario}
                disabled={loading}
                className="py-2.5 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-all cursor-pointer active:scale-95 flex items-center justify-center"
                title="Reload Scenario Settings"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <button
              onClick={handleStopScenario}
              disabled={loading}
              className="w-full py-2.5 rounded-xl text-xs font-black uppercase tracking-wider bg-rose-500 hover:bg-rose-400 text-white transition-all disabled:opacity-50 cursor-pointer flex items-center justify-center gap-1.5 active:scale-95"
            >
              <Square className="w-3.5 h-3.5" /> Abort Scenario
            </button>
          )}
        </div>

        {/* Active shedded meters listing */}
        {scenarioStatus.shedded_meters.length > 0 && (
          <div className="bg-rose-500/10 p-4 rounded-2xl border border-rose-500/20 space-y-2">
            <div className="flex items-center gap-1.5 text-xs font-black text-rose-400 uppercase tracking-wider">
              <AlertTriangle className="w-4 h-4" /> Shedded Meters ({scenarioStatus.shedded_meters.length})
            </div>
            <div className="flex flex-wrap gap-1.5">
              {scenarioStatus.shedded_meters.map(id => (
                <span key={id} className="text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30 px-2 py-0.5 rounded-md flex items-center gap-1">
                  <Power className="w-2.5 h-2.5" /> {id}
                </span>
              ))}
            </div>
          </div>
        )}

        {scenarioStatus.scenario_loaded && !scenarioStatus.is_active && (
          <div className="bg-slate-900/50 p-4 rounded-2xl border border-white/5 flex gap-2 items-start text-[11px] text-slate-500 leading-normal">
            <Info className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
            <p>
              {scenarioStatus.latency_enabled
                ? "Ready to run with cyber-network delay. Active meters will go offline with geographic latency offsets to simulate point-to-point ns-3 delays."
                : "Ready to start. Dynamic scenario will drop configured smart meters sequentially to evaluate grid stabilization capabilities."}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
