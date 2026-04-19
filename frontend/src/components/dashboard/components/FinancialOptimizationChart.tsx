import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';

interface OptimizationData {
  hour: number;
  p_grid_mw: number;
  p_bess_mw: number;
  p_diesel_mw: number;
  hourly_cost_thb: number;
  savings_vs_diesel_thb: number;
}

interface FinancialOptimizationChartProps {
  data: OptimizationData[];
}

export const FinancialOptimizationChart: React.FC<FinancialOptimizationChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-slate-500 bg-slate-900/40 rounded-2xl border border-white/5">
        No financial optimization data available.
      </div>
    );
  }

  return (
    <div className="glass rounded-3xl p-6 border border-white/10 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-black uppercase tracking-widest text-slate-400">
          Game Theory Strategy Dispatch
        </h2>
        <div className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
          13 THB Penalty Avoidance Active
        </div>
      </div>
      
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorGrid" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#818cf8" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#818cf8" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorBess" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#34d399" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#34d399" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorDiesel" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#fb7185" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#fb7185" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis 
              dataKey="hour" 
              stroke="#64748b" 
              tickFormatter={(val) => `${val}:00`}
              tick={{ fontSize: 12 }} 
            />
            <YAxis 
              stroke="#64748b" 
              tick={{ fontSize: 12 }}
              label={{ value: 'MW', angle: -90, position: 'insideLeft', fill: '#64748b' }}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
              itemStyle={{ fontSize: '14px', fontWeight: 'bold' }}
              labelStyle={{ color: '#94a3b8', marginBottom: '8px' }}
            />
            <Legend wrapperStyle={{ paddingTop: '20px' }} />
            <Area 
              type="monotone" 
              dataKey="p_grid_mw" 
              name="Grid Import (2.5 THB)" 
              stroke="#818cf8" 
              fillOpacity={1} 
              fill="url(#colorGrid)" 
              stackId="1"
            />
            <Area 
              type="monotone" 
              dataKey="p_bess_mw" 
              name="BESS Discharge (3.5 THB)" 
              stroke="#34d399" 
              fillOpacity={1} 
              fill="url(#colorBess)" 
              stackId="1"
            />
            <Area 
              type="monotone" 
              dataKey="p_diesel_mw" 
              name="Diesel Generator (13 THB)" 
              stroke="#fb7185" 
              fillOpacity={1} 
              fill="url(#colorDiesel)" 
              stackId="1"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      
      {/* Mini cost breakdown */}
      <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-white/5">
         <div className="bg-slate-900/40 p-4 rounded-2xl border border-white/5">
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">24h Estimated Cost</span>
            <div className="text-xl font-black text-rose-400 mt-1">
              {(data.reduce((sum, d) => sum + d.hourly_cost_thb, 0)).toLocaleString(undefined, { maximumFractionDigits: 0 })} <span className="text-xs text-slate-500">THB</span>
            </div>
         </div>
         <div className="bg-slate-900/40 p-4 rounded-2xl border border-white/5">
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">24h Potential Savings</span>
            <div className="text-xl font-black text-emerald-400 mt-1">
              {(data.reduce((sum, d) => sum + d.savings_vs_diesel_thb, 0)).toLocaleString(undefined, { maximumFractionDigits: 0 })} <span className="text-xs text-slate-500">THB</span>
            </div>
         </div>
      </div>
    </div>
  );
};
