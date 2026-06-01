"use client";

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  Coins, 
  Flame, 
  Leaf, 
  Activity, 
  Sparkles,
  RefreshCw,
  Info
} from 'lucide-react';
import { useNetwork } from '@/components/providers/NetworkProvider';
import { useSimulator } from '@/components/providers/SimulatorProvider';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  Legend
} from 'recharts';

interface CostRecord {
  timestamp: string;
  zone: string;
  source: 'Solar' | 'BESS' | 'Diesel' | 'Grid';
  cost_thb: number;
  savings_thb: number;
  carbon_tax_thb: number;
  strategy_mode: string;
  meter_id: string;
  diesel_displaced_liters?: number;
  carbon_offset_kg?: number;
}

interface SavingsSummary {
  total_savings_thb: number;
  diesel_displaced_liters: number;
  carbon_offset_kg: number;
}

export function FinancialsTab() {
  const { getApiUrl } = useNetwork();
  const { status } = useSimulator();

  const [costs, setCosts] = useState<CostRecord[]>([]);
  const [summary, setSummary] = useState<SavingsSummary>({
    total_savings_thb: 0.0,
    diesel_displaced_liters: 0.0,
    carbon_offset_kg: 0.0
  });
  const [loading, setLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);

  const fetchFinancialData = useCallback(async () => {
    try {
      const [costsRes, summaryRes] = await Promise.all([
        fetch(getApiUrl('/api/v1/analytics/costs')),
        fetch(getApiUrl('/api/v1/analytics/savings/summary'))
      ]);

      if (costsRes.ok && summaryRes.ok) {
        const costsData = await costsRes.json();
        const summaryData = await summaryRes.json();
        setCosts(costsData);
        setSummary(summaryData);
      }
    } catch (error) {
      console.error('Error fetching financial data:', error);
    } finally {
      setLoading(false);
    }
  }, [getApiUrl]);

  // Poll for updates when the simulator is running
  useEffect(() => {
    fetchFinancialData();
    
    // Set up polling interval
    const intervalTime = status.running ? 2000 : 5000;
    const interval = setInterval(fetchFinancialData, intervalTime);
    
    return () => clearInterval(interval);
  }, [fetchFinancialData, status.running, refreshKey]);

  // Aggregate costs by source
  const sourceTotals = useMemo(() => {
    const totals = {
      Grid: 0,
      BESS: 0,
      Diesel: 0,
      Solar: 0
    };
    
    costs.forEach(record => {
      if (totals[record.source] !== undefined) {
        totals[record.source] += record.cost_thb;
      }
    });

    return [
      { name: 'Grid Import', value: totals.Grid, color: '#6366f1' }, // Indigo
      { name: 'BESS LCOS', value: totals.BESS, color: '#f59e0b' },   // Amber
      { name: 'Diesel Fuel', value: totals.Diesel, color: '#f43f5e' }, // Rose
      { name: 'Solar Direct', value: totals.Solar, color: '#10b981' }  // Emerald
    ];
  }, [costs]);

  // Aggregate carbon tax
  const totalCarbonTax = useMemo(() => {
    return costs.reduce((sum, r) => sum + r.carbon_tax_thb, 0);
  }, [costs]);

  // Aggregate direct costs
  const totalDirectCost = useMemo(() => {
    return costs.reduce((sum, r) => sum + r.cost_thb, 0);
  }, [costs]);

  // Calculate Net Financial Benefit
  const netBenefit = useMemo(() => {
    return summary.total_savings_thb - totalDirectCost - totalCarbonTax;
  }, [summary.total_savings_thb, totalDirectCost, totalCarbonTax]);

  // Process historical data for the area chart
  const timelineData = useMemo(() => {
    const groups: Record<string, { timestamp: string; Grid: number; BESS: number; Diesel: number; Solar: number; cost: number; savings: number; tax: number }> = {};
    
    // Group records by unique timestamp
    costs.forEach(r => {
      const time = r.timestamp;
      if (!groups[time]) {
        groups[time] = {
          timestamp: time,
          Grid: 0,
          BESS: 0,
          Diesel: 0,
          Solar: 0,
          cost: 0,
          savings: 0,
          tax: 0
        };
      }
      groups[time][r.source] += r.cost_thb;
      groups[time].cost += r.cost_thb;
      groups[time].savings += r.savings_thb;
      groups[time].tax += r.carbon_tax_thb;
    });

    // Convert to sorted array and calculate cumulative values
    const sortedTimestamps = Object.keys(groups).sort();
    let cumulativeCost = 0;
    let cumulativeSavings = 0;
    let cumulativeNet = 0;

    return sortedTimestamps.map((ts, idx) => {
      const g = groups[ts];
      cumulativeCost += g.cost;
      cumulativeSavings += g.savings;
      cumulativeNet += (g.savings - g.cost - g.tax);
      
      // Formatting time to hh:mm:ss
      let timeLabel = `Step ${idx + 1}`;
      try {
        const date = new Date(ts);
        timeLabel = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      } catch (e) {}

      return {
        time: timeLabel,
        'Direct Cost': Math.round(g.cost * 10) / 10,
        'Avoided Cost Savings': Math.round(g.savings * 10) / 10,
        'Carbon Tax': Math.round(g.tax * 10) / 10,
        'Cumulative Direct Cost': Math.round(cumulativeCost * 10) / 10,
        'Cumulative Savings': Math.round(cumulativeSavings * 10) / 10,
        'Cumulative Net Benefit': Math.round(cumulativeNet * 10) / 10
      };
    });
  }, [costs]);

  if (loading && costs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-slate-500 border border-dashed border-slate-700/50 rounded-2xl bg-slate-900/20 min-h-[400px]">
        <RefreshCw className="w-10 h-10 mb-4 animate-spin text-emerald-400" />
        <h3 className="text-lg font-bold text-slate-400 mb-1">Loading Financial Ledger</h3>
        <p className="text-sm opacity-60">Synchronizing transaction rates and avoided cost structures...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Financial Overview Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Card 1: Avoided Cost (Savings) */}
        <div className="relative overflow-hidden group rounded-2xl border border-emerald-500/20 bg-slate-900/60 backdrop-blur-xl p-5 shadow-lg transition-all hover:border-emerald-500/40">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:scale-110 transition-transform duration-300">
            <Coins className="w-24 h-24 text-emerald-400" />
          </div>
          <div className="flex justify-between items-start">
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Avoided Diesel Savings</span>
            <span className="flex items-center gap-1 text-[10px] font-black uppercase tracking-widest text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full">
              <Sparkles className="w-3 h-3" /> DER Offset
            </span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black text-emerald-400 tracking-tight">
              {summary.total_savings_thb.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            <span className="text-sm font-bold text-slate-400">THB</span>
          </div>
          
          <div className="mt-4 pt-3 border-t border-white/5 grid grid-cols-2 gap-4">
            <div>
              <span className="text-[9px] font-bold text-slate-500 block uppercase">Diesel Displaced</span>
              <span className="text-sm font-black text-slate-300 flex items-center gap-1.5 mt-0.5">
                <Flame className="w-3.5 h-3.5 text-rose-400" />
                {summary.diesel_displaced_liters.toLocaleString(undefined, { maximumFractionDigits: 1 })} L
              </span>
            </div>
            <div>
              <span className="text-[9px] font-bold text-slate-500 block uppercase">Carbon Offsets</span>
              <span className="text-sm font-black text-emerald-400 flex items-center gap-1.5 mt-0.5">
                <Leaf className="w-3.5 h-3.5" />
                {summary.carbon_offset_kg.toLocaleString(undefined, { maximumFractionDigits: 1 })} kg
              </span>
            </div>
          </div>
        </div>

        {/* Card 2: Direct Cost & Tax */}
        <div className="relative overflow-hidden group rounded-2xl border border-white/10 bg-slate-900/60 backdrop-blur-xl p-5 shadow-lg transition-all hover:border-indigo-500/20">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:scale-110 transition-transform duration-300">
            <TrendingDown className="w-24 h-24 text-rose-400" />
          </div>
          <div className="flex justify-between items-start">
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Gross Operational Costs</span>
            <span className="text-[10px] font-black uppercase tracking-widest text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-full">
              LMP + Fuel
            </span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-200 tracking-tight">
              {(totalDirectCost + totalCarbonTax).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            <span className="text-sm font-bold text-slate-400">THB</span>
          </div>

          <div className="mt-4 pt-3 border-t border-white/5 grid grid-cols-2 gap-4">
            <div>
              <span className="text-[9px] font-bold text-slate-500 block uppercase">Direct Energy Cost</span>
              <span className="text-sm font-black text-slate-300 mt-0.5 block">
                {totalDirectCost.toLocaleString(undefined, { maximumFractionDigits: 1 })} THB
              </span>
            </div>
            <div>
              <span className="text-[9px] font-bold text-slate-500 block uppercase">Carbon Tax Liability</span>
              <span className="text-sm font-black text-rose-400 mt-0.5 block">
                {totalCarbonTax.toLocaleString(undefined, { maximumFractionDigits: 1 })} THB
              </span>
            </div>
          </div>
        </div>

        {/* Card 3: Net Benefit */}
        <div className={`relative overflow-hidden group rounded-2xl border bg-slate-900/60 backdrop-blur-xl p-5 shadow-lg transition-all ${
          netBenefit >= 0 ? 'border-indigo-500/20 hover:border-indigo-500/40' : 'border-rose-500/20 hover:border-rose-500/40'
        }`}>
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:scale-110 transition-transform duration-300">
            <TrendingUp className="w-24 h-24 text-indigo-400" />
          </div>
          <div className="flex justify-between items-start">
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Net Economic Surplus</span>
            <span className={`text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full ${
              netBenefit >= 0 ? 'text-indigo-400 bg-indigo-500/10' : 'text-rose-400 bg-rose-500/10'
            }`}>
              Net ROI
            </span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className={`text-3xl font-black tracking-tight ${netBenefit >= 0 ? 'text-indigo-400' : 'text-rose-400'}`}>
              {netBenefit.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            <span className="text-sm font-bold text-slate-400">THB</span>
          </div>

          <div className="mt-4 pt-3 border-t border-white/5 grid grid-cols-2 gap-4">
            <div>
              <span className="text-[9px] font-bold text-slate-500 block uppercase">ROI Efficiency</span>
              <span className={`text-sm font-black mt-0.5 block ${netBenefit >= 0 ? 'text-indigo-400' : 'text-rose-400'}`}>
                {totalDirectCost > 0 ? `${Math.round((summary.total_savings_thb / (totalDirectCost + totalCarbonTax)) * 100)}%` : '100%'}
              </span>
            </div>
            <div>
              <span className="text-[9px] font-bold text-slate-500 block uppercase">Strategy Mode</span>
              <span className="text-sm font-black text-slate-300 mt-0.5 block truncate">
                {costs[costs.length - 1]?.strategy_mode || 'NORMAL'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {costs.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 text-slate-500 border border-dashed border-slate-700/50 rounded-2xl bg-slate-900/20 min-h-[300px]">
          <Info className="w-10 h-10 mb-4 text-slate-400 opacity-60" />
          <h3 className="text-lg font-bold text-slate-400 mb-1">No Financial Data Recorded</h3>
          <p className="text-sm opacity-60 text-center max-w-md">
            Start the simulation and dispatch DER resources (BESS/Solar) to populate economic transaction metrics.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Timeline Cumulative Performance */}
          <div className="lg:col-span-2 rounded-2xl border border-white/10 bg-slate-900/40 p-5 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-black uppercase tracking-widest text-slate-400 flex items-center gap-2">
                <Activity className="w-4 h-4 text-indigo-400" /> Economic Performance Timeline
              </h3>
              <button 
                onClick={() => setRefreshKey(k => k + 1)}
                className="p-1.5 hover:bg-white/5 rounded-lg transition-colors text-slate-500 hover:text-slate-300"
                title="Refresh Ledger"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>
            
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={timelineData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorCost" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorSavings" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorNet" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis 
                    dataKey="time" 
                    stroke="#475569" 
                    tick={{ fontSize: 10 }} 
                  />
                  <YAxis 
                    stroke="#475569" 
                    tick={{ fontSize: 10 }}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                    itemStyle={{ fontSize: '13px', fontWeight: 'bold' }}
                    labelStyle={{ color: '#94a3b8', marginBottom: '4px', fontSize: '11px' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                  <Area 
                    type="monotone" 
                    dataKey="Cumulative Direct Cost" 
                    stroke="#f43f5e" 
                    strokeWidth={2}
                    fillOpacity={1} 
                    fill="url(#colorCost)" 
                  />
                  <Area 
                    type="monotone" 
                    dataKey="Cumulative Savings" 
                    stroke="#10b981" 
                    strokeWidth={2}
                    fillOpacity={1} 
                    fill="url(#colorSavings)" 
                  />
                  <Area 
                    type="monotone" 
                    dataKey="Cumulative Net Benefit" 
                    stroke="#6366f1" 
                    strokeWidth={2.5}
                    fillOpacity={1} 
                    fill="url(#colorNet)" 
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Cost Allocation by Asset Type */}
          <div className="rounded-2xl border border-white/10 bg-slate-900/40 p-5 space-y-4">
            <h3 className="text-sm font-black uppercase tracking-widest text-slate-400">
              Direct Cost Allocation
            </h3>
            
            <div className="h-60 w-full flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sourceTotals} layout="vertical" margin={{ top: 5, right: 10, left: 15, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                  <XAxis type="number" stroke="#475569" tick={{ fontSize: 10 }} />
                  <YAxis dataKey="name" type="category" stroke="#475569" tick={{ fontSize: 10 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                    formatter={(value) => [`${value} THB`, 'Cost']}
                  />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={16}>
                    {sourceTotals.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Source breakdown legend with totals */}
            <div className="space-y-1.5 text-xs">
              {sourceTotals.map((source, index) => (
                <div key={index} className="flex justify-between items-center py-1 border-b border-white/5 last:border-0">
                  <div className="flex items-center gap-2 text-slate-400">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: source.color }} />
                    {source.name}
                  </div>
                  <div className="font-bold text-slate-200">
                    {source.value.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} THB
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
