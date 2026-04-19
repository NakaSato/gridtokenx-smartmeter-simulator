"use client";

import { useState, useEffect, useCallback } from 'react';
import { 
  Zap, 
  Map as MapIcon, 
  TrendingUp, 
  Leaf, 
  AlertCircle, 
  Activity,
  ArrowRight,
  ShieldCheck,
  Globe,
  Coins
} from 'lucide-react';
import { useNetwork } from '@/components/providers/NetworkProvider';

interface SummaryData {
  timestamp: string;
  grid: {
    avg_loading_percent: number;
    num_buses: number;
    num_lines: number;
  };
  market: {
    min_nodal_price: number;
    max_nodal_price: number;
    avg_nodal_price: number;
    avg_consumer_price: number;
    avg_prosumer_price: number;
    last_matches_count: number;
    currency: string;
  };
  environmental: {
    carbon_intensity_g_kwh: number;
    grid_status: string;
  };
  simulation: {
    running: boolean;
    mode: string;
    num_meters: number;
    num_consumers: number;
    num_prosumers: number;
  };
}

const LPCDashboard = () => {
  const { getApiUrl } = useNetwork();
  const [data, setData] = useState<SummaryData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = useCallback(async () => {
    try {
      const res = await fetch(getApiUrl('/api/v1/analytics/summary'));
      if (!res.ok) throw new Error('Failed to fetch summary');
      const json = await res.json();
      setData(json);
      setError(null);
    } catch (err) {
      console.error('Summary fetch error:', err);
      setError('Connection lost to simulator backend.');
    }
  }, [getApiUrl]);

  useEffect(() => {
    fetchSummary();
    const interval = setInterval(fetchSummary, 3000);
    return () => clearInterval(interval);
  }, [fetchSummary]);

  if (!data) {
    return (
      <div className="min-h-screen bg-[#050505] text-white flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin"></div>
          <p className="text-slate-500 font-medium animate-pulse uppercase tracking-[0.2em] text-xs">Syncing Grid Metadata...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#050505] text-slate-300 p-6 lg:p-10 selection:bg-indigo-500/30">
      {/* Header */}
      <header className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-6 mb-12">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-500/10 rounded-lg">
              <Activity className="w-5 h-5 text-indigo-400" />
            </div>
            <h1 className="text-2xl font-black text-white tracking-tight uppercase">Green Grid <span className="text-indigo-500">Analytics</span></h1>
          </div>
          <p className="text-sm text-slate-500 font-medium">LMP Congestion & Carbon Intensity Pulse</p>
        </div>
        
        <div className="flex items-center gap-4">
          <div className={`px-4 py-2 rounded-full border ${data.simulation?.running ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-rose-500/10 border-rose-500/20 text-rose-400'} flex items-center gap-2 text-xs font-black uppercase tracking-widest`}>
            <div className={`w-1.5 h-1.5 rounded-full ${data.simulation?.running ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
            {data.simulation?.running ? 'Live' : 'Stopped'}
          </div>
          <div className="text-[10px] font-mono text-slate-600 bg-white/5 px-3 py-1.5 rounded-lg border border-white/5">
            {new Date(data.timestamp).toLocaleTimeString()}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto space-y-8">
        {/* KPI Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          
          {/* Consumer Pulse (Phase 25) */}
          <section className="glass p-8 rounded-[2.5rem] border-indigo-500/10 relative overflow-hidden group hover:border-blue-500/30 transition-all duration-500 bg-blue-500/5">
            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 blur-[60px] rounded-full group-hover:bg-blue-500/20 transition-all" />
            <div className="relative space-y-6">
              <div className="flex justify-between items-start">
                <div className="p-4 bg-blue-500/10 rounded-2xl text-blue-400 group-hover:scale-110 transition-transform">
                  <ShieldCheck className="w-6 h-6" />
                </div>
                <span className="text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-full bg-blue-500/20 text-blue-400">
                  {data.simulation?.num_consumers} METERED
                </span>
              </div>
              <div>
                <h3 className="text-sm font-black text-slate-500 uppercase tracking-widest mb-1">Consumer Price</h3>
                <div className="flex items-baseline gap-2">
                  <span className="text-5xl font-black text-white">{data.market?.avg_consumer_price?.toFixed(2) ?? '—'}</span>
                  <span className="text-slate-500 font-bold">THB</span>
                </div>
              </div>
              <div className="pt-4 border-t border-white/5 flex items-center justify-between">
                <span className="text-xs text-slate-500 font-bold">Consumption Unit Rate</span>
                <TrendingUp className="w-4 h-4 text-blue-500/50" />
              </div>
            </div>
          </section>
          
          {/* Carbon Insight */}
          <section className="glass p-8 rounded-[2.5rem] relative overflow-hidden group hover:border-emerald-500/30 transition-all duration-500">
            <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 blur-[60px] rounded-full group-hover:bg-emerald-500/20 transition-all" />
            <div className="relative space-y-6">
              <div className="flex justify-between items-start">
                <div className="p-4 bg-emerald-500/10 rounded-2xl text-emerald-400 group-hover:scale-110 transition-transform">
                  <Leaf className="w-6 h-6" />
                </div>
                <span className={`text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-full ${data.environmental?.grid_status === 'Clean' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'}`}>
                  {data.environmental?.grid_status ?? '—'} Grid
                </span>
              </div>
              <div>
                <h3 className="text-sm font-black text-slate-500 uppercase tracking-widest mb-1">Carbon Intensity</h3>
                <div className="flex items-baseline gap-2">
                  <span className="text-5xl font-black text-white">{data.environmental?.carbon_intensity_g_kwh?.toFixed(1) ?? '—'}</span>
                  <span className="text-slate-500 font-bold">g/kWh</span>
                </div>
              </div>
              <div className="pt-4 border-t border-white/5 flex items-center justify-between">
                <span className="text-xs text-slate-500 font-bold">Environmental Status</span>
                <Globe className="w-4 h-4 text-emerald-500/50" />
              </div>
            </div>
          </section>

          {/* Market / LMP */}
          <section className="glass p-8 rounded-[2.5rem] relative overflow-hidden group hover:border-amber-500/30 transition-all duration-500">
            <div className="absolute top-0 right-0 w-32 h-32 bg-amber-500/10 blur-[60px] rounded-full group-hover:bg-amber-500/20 transition-all" />
            <div className="relative space-y-6">
              <div className="flex justify-between items-start">
                <div className="p-4 bg-amber-500/10 rounded-2xl text-amber-400 group-hover:scale-110 transition-transform">
                  <TrendingUp className="w-6 h-6" />
                </div>
                <div className="flex items-center gap-1.5 text-xs text-amber-500 font-black uppercase">
                  <Activity className="w-3.5 h-3.5" />
                  Volatile
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Market Avg</h3>
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-black text-white">{data.market?.avg_nodal_price?.toFixed(2) ?? '—'}</span>
                    <span className="text-[10px] text-slate-600 font-black">THB</span>
                  </div>
                </div>
                <div>
                  <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Max LMP</h3>
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-black text-rose-500">{data.market?.max_nodal_price?.toFixed(2) ?? '—'}</span>
                  </div>
                </div>
              </div>
              <div className="pt-4 border-t border-white/5 flex items-center justify-between">
                <span className="text-xs text-slate-500 font-bold">Congestion Pricing</span>
                <ShieldCheck className="w-4 h-4 text-amber-500/50" />
              </div>
            </div>
          </section>

          {/* Grid Health */}
          <section className="glass p-8 rounded-[2.5rem] relative overflow-hidden group hover:border-indigo-500/30 transition-all duration-500">
            <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 blur-[60px] rounded-full group-hover:bg-indigo-500/20 transition-all" />
            <div className="relative space-y-6">
              <div className="flex justify-between items-start">
                <div className="p-4 bg-indigo-500/10 rounded-2xl text-indigo-400 group-hover:scale-110 transition-transform">
                  <Zap className="w-6 h-6" />
                </div>
                <div className="flex items-center gap-1.5 text-xs text-indigo-400 font-black uppercase">
                   {data.grid?.num_buses ?? '—'} Nodes
                </div>
              </div>
              <div>
                <h3 className="text-sm font-black text-slate-500 uppercase tracking-widest mb-1">Avg Line Loading</h3>
                <div className="flex items-baseline gap-2">
                  <span className={`text-5xl font-black ${(data.grid?.avg_loading_percent ?? 0) > 85 ? 'text-rose-500' : 'text-white'}`}>
                    {data.grid?.avg_loading_percent?.toFixed(1) ?? '—'}
                  </span>
                  <span className="text-slate-500 font-bold">%</span>
                </div>
              </div>
              <div className="pt-4 border-t border-white/5 flex items-center justify-between">
                <span className="text-xs text-slate-500 font-bold">Thermal Stress</span>
                <div className="flex gap-1">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className={`w-1.5 h-1.5 rounded-full ${i < ((data.grid?.avg_loading_percent ?? 0) / 20) ? 'bg-indigo-500' : 'bg-white/10'}`} />
                  ))}
                </div>
              </div>
            </div>
          </section>
        </div>

        {/* Detailed Insights */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="glass p-8 rounded-[2.5rem] space-y-6">
                <div className="flex justify-between items-center">
                    <h2 className="text-lg font-black text-white uppercase tracking-tight">System Performance</h2>
                    <Coins className="w-5 h-5 text-slate-600" />
                </div>
                <div className="space-y-4">
                    <div className="flex justify-between p-4 bg-white/5 rounded-2xl border border-white/5">
                        <span className="text-sm font-bold">P2P Transactions</span>
                        <span className="text-sm font-black text-indigo-400">{data.market?.last_matches_count ?? 0} matches</span>
                    </div>
                    <div className="flex justify-between p-4 bg-white/5 rounded-2xl border border-white/5">
                        <span className="text-sm font-bold">Simulation Mode</span>
                        <span className="text-sm font-black text-white capitalize">{data.simulation?.mode}</span>
                    </div>
                    <div className="flex justify-between p-4 bg-white/5 rounded-2xl border border-white/5">
                        <span className="text-sm font-bold">Network Density</span>
                        <div className="text-right">
                             <div className="text-sm font-black text-white">{data.simulation?.num_prosumers} Prosumers</div>
                             <div className="text-[10px] text-slate-500 font-bold">{data.simulation?.num_consumers} Consumers</div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="glass p-8 rounded-[2.5rem] flex flex-col justify-center gap-6 bg-gradient-to-br from-indigo-500/10 to-transparent">
                <div className="p-5 bg-indigo-500 rounded-3xl w-fit shadow-xl shadow-indigo-500/20">
                    <MapIcon className="w-8 h-8 text-white" />
                </div>
                <div>
                   <h2 className="text-2xl font-black text-white uppercase">Topology Explorer</h2>
                   <p className="text-slate-500 font-medium max-w-sm mt-2">
                    Nodal prices are calculated using PandaPower with Locational Marginal Pricing (Phase 21).
                   </p>
                </div>
                <button className="flex items-center gap-3 text-indigo-400 font-black uppercase text-xs tracking-[0.2em] group">
                    Explore Grid Map
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-2 transition-transform" />
                </button>
            </div>
        </div>

        {error && (
            <div className="fixed bottom-10 left-10 right-10 flex justify-center">
                <div className="bg-rose-500 text-white px-6 py-3 rounded-2xl shadow-2xl flex items-center gap-3 animate-bounce">
                    <AlertCircle className="w-5 h-5" />
                    <span className="text-sm font-black uppercase tracking-widest">{error}</span>
                </div>
            </div>
        )}
      </main>
    </div>
  );
};

export default LPCDashboard;
