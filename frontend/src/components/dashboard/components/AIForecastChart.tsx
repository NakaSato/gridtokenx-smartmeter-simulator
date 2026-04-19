import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';

interface AIForecastData {
  timestamp: string;
  hour_offset: number;
  Load_Tao: number;
  Capacity_115kV: number;
  delta: number;
  constraint_active: boolean;
  DAP_d?: number;
  T_active?: number;
  thermal_derating_kw?: number;
}

interface AIForecastChartProps {
  data: AIForecastData[];
}

export const AIForecastChart: React.FC<AIForecastChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return null;
  }

  // Find the exact bottleneck hours (where capacity < load)
  const bottleneckHours = data.filter(d => d.delta < 0);
  const nextBottleneck = bottleneckHours.length > 0 ? bottleneckHours[0] : null;
  const currentDap = data.length > 0 ? data[0].DAP_d : null;
  const currentActiveTourists = data.length > 0 ? data[0].T_active : null;
  const maxThermalDerating = data.reduce((max, d) => Math.max(max, d.thermal_derating_kw || 0), 0);

  return (
    <div className="glass rounded-3xl p-6 border border-white/10 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-black uppercase tracking-widest text-slate-400">
          AI Load Forecast vs Transmission Capacity
        </h2>
        {nextBottleneck ? (
          <div className="text-xs font-bold text-rose-400 bg-rose-500/10 px-3 py-1 rounded-full border border-rose-500/20 animate-pulse">
            Bottleneck Predicted in {nextBottleneck.hour_offset} hours
          </div>
        ) : (
          <div className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
            Capacity Sufficient (Next 24h)
          </div>
        )}
      </div>
      
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis 
              dataKey="timestamp" 
              stroke="#64748b" 
              tickFormatter={(val) => new Date(val).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              tick={{ fontSize: 12 }} 
            />
            <YAxis 
              stroke="#64748b" 
              tick={{ fontSize: 12 }}
              label={{ value: 'kW', angle: -90, position: 'insideLeft', fill: '#64748b' }}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
              itemStyle={{ fontSize: '14px', fontWeight: 'bold' }}
              labelStyle={{ color: '#94a3b8', marginBottom: '8px' }}
              labelFormatter={(label) => new Date(label).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              formatter={(value: any, name: any, props: any) => {
                if (name === "Koh Tao Load (Demand)" && props.payload.DAP_d) {
                  return [
                    <div key={name}>
                      <div>{Number(value).toLocaleString()} kW</div>
                      <div className="text-xs font-normal text-slate-400 mt-1">
                        Driven by DAP: {props.payload.DAP_d.toLocaleString()}
                      </div>
                    </div>,
                    name
                  ];
                }
                if (name === "115kV Cable Capacity" && props.payload.thermal_derating_kw > 0) {
                  return [
                    <div key={name}>
                      <div>{Number(value).toLocaleString()} kW</div>
                      <div className="text-xs font-bold text-orange-400 mt-1">
                        Thermal Penalty: -{props.payload.thermal_derating_kw.toLocaleString()} kW
                      </div>
                    </div>,
                    name
                  ];
                }
                return [Number(value).toLocaleString() + ' kW', name];
              }}
            />
            <Legend wrapperStyle={{ paddingTop: '20px' }} />
            <Line 
              type="monotone" 
              dataKey="Load_Tao" 
              name="Koh Tao Load (Demand)" 
              stroke="#eab308" 
              strokeWidth={3}
              dot={false}
              activeDot={{ r: 6 }}
            />
            <Line 
              type="monotone" 
              dataKey="Capacity_115kV" 
              name="115kV Cable Capacity" 
              stroke="#3b82f6" 
              strokeWidth={3}
              dot={false}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      {/* Mini Insights */}
      <div className="mt-4 pt-4 border-t border-white/5 flex flex-col gap-2 text-sm">
        {currentDap && (
          <div className="text-slate-400 flex items-center justify-between bg-slate-800/50 p-3 rounded-lg border border-slate-700/50">
            <div>
              <span className="font-bold text-indigo-400">Demographic Baseline: </span>
              <span className="text-slate-300">Daily Active Population (DAP)</span>
            </div>
            <div className="flex gap-4">
              <div className="text-right">
                <div className="text-lg font-bold text-white">{currentDap.toLocaleString()}</div>
                <div className="text-xs text-slate-500">Total Population</div>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-emerald-400">{(currentActiveTourists || 0).toLocaleString()}</div>
                <div className="text-xs text-slate-500">Active Tourists</div>
              </div>
            </div>
          </div>
        )}
        
        {maxThermalDerating > 0 && (
          <div className="text-slate-400 flex items-center justify-between bg-orange-500/10 p-3 rounded-lg border border-orange-500/20">
            <div>
              <span className="font-bold text-orange-400">Thermal Penalty Active: </span>
              <span className="text-slate-300">Cable Dynamic Line Rating (DLR)</span>
            </div>
            <div className="text-right">
              <div className="text-lg font-bold text-orange-400">-{maxThermalDerating.toLocaleString()} kW</div>
              <div className="text-xs text-slate-500">Max Capacity Derating</div>
            </div>
          </div>
        )}
        
        {nextBottleneck && (
          <div className="text-slate-400 mt-2">
            <span className="font-bold text-rose-400">Action Required: </span>
            BESS dispatch needed at {new Date(nextBottleneck.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} to cover {Math.abs(nextBottleneck.delta).toLocaleString(undefined, { maximumFractionDigits: 0 })} kW deficit.
          </div>
        )}
      </div>
    </div>
  );
};
