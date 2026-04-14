"use client";

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { 
    ChevronLeft, 
    Zap, 
    Sun, 
    CreditCard, 
    History, 
    Activity,
    ArrowUpRight,
    ArrowDownRight,
    MapPin,
    Wallet,
    Coins,
    Globe,
    Cpu,
    RefreshCw,
    TrendingUp
} from 'lucide-react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell
} from 'recharts';
import { useNetwork } from '@/components/providers/NetworkProvider';
import { StatCard } from '@/components/ui/StatCard';

interface MeterMetadata {
    meter_id: string;
    serial_number: string;
    meter_type: string;
    location_name: string;
    latitude: number;
    longitude: number;
    phase: string;
    solar_capacity: number;
    has_battery: boolean;
    has_solar: boolean;
    wallet_address: string;
}

interface HistoryItem {
    timestamp: string;
    type: string;
    amount_kwh: number;
    price: number;
    total: number;
    counterparty: string | null;
    is_p2p: boolean;
}

interface BillingItem {
    month: number;
    year: number;
    total_kwh: number;
    net_amount: number;
    carbon_saved: number;
    status: string;
}

interface WalletData {
    meter_id: string;
    balances: {
        thb: number;
        sol: number;
        gtnx: number;
    };
    onchain_grx?: number;
    onchain_sol?: number;
    is_synced_with_solana?: boolean;
    blockchain_address?: string;
    stats: {
        grid_import_kwh: number;
        grid_export_kwh: number;
        p2p_volume_kwh: number;
        green_rewards_earned: number;
    };
    timestamp: string | null;
}

const MeterDetails = () => {
    const { meterId } = useParams<{ meterId: string }>();
    const { getApiUrl } = useNetwork();
    
    const [metadata, setMetadata] = useState<MeterMetadata | null>(null);
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [billing, setBilling] = useState<BillingItem[]>([]);
    const [stats, setStats] = useState<{ 
        total_gen_kwh: number; 
        total_cons_kwh: number;
        total_solar_self_kwh: number;
        p2p_participation_kwh: number;
        total_revenue_baht: number;
        total_cost_baht: number;
        net_financial_baht: number;
    } | null>(null);
    const [wallet, setWallet] = useState<WalletData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        if (!meterId) return;

        try {
            const [metaRes, histRes, billRes, walletRes] = await Promise.all([
                fetch(getApiUrl(`/api/v1/meters/${meterId}`)),
                fetch(getApiUrl(`/api/v1/meters/${meterId}/readings?limit=50`)),
                fetch(getApiUrl(`/api/v1/meters/${meterId}/bills/history`)),
                fetch(getApiUrl(`/api/v1/meters/${meterId}/wallet`))
            ]);

            if (!metaRes.ok) throw new Error(`Metadata Error: ${metaRes.status}`);
            if (!histRes.ok) throw new Error(`History Error: ${histRes.status}`);
            if (!billRes.ok) throw new Error(`Billing Error: ${billRes.status}`);
            if (!walletRes.ok) throw new Error(`Wallet Error: ${walletRes.status}`);

            const metaData = await metaRes.json();
            const histData = await histRes.json();
            const billData = await billRes.json();
            const walletResData = await walletRes.json();

            setMetadata(metaData);
            setHistory(histData.history || histData.readings || []);
            setStats(histData.stats || null);
            setBilling(billData.history || billData.bills || []);
            setWallet(walletResData);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setLoading(false);
        }
    }, [meterId, getApiUrl]);

    const handleAirdrop = async () => {
        if (!meterId) return;
        try {
            const res = await fetch(getApiUrl(`/api/v1/meters/${meterId}/wallet/airdrop`), { method: 'POST' });
            if (res.ok) {
                fetchData(); // Refresh wallet
            }
        } catch (err) {
            console.error("Airdrop failed", err);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, [fetchData]);

    if (loading && !metadata) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    if (error || !metadata) {
        return (
            <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-center">
                <div className="w-16 h-16 bg-rose-500/20 rounded-full flex items-center justify-center mb-4">
                    <Activity className="w-8 h-8 text-rose-500" />
                </div>
                <h2 className="text-2xl font-black text-white mb-2 uppercase">Meter Not Found</h2>
                <p className="text-slate-400 mb-6">{error || `Could not find data for ${meterId}`}</p>
                <Link href="/map" className="px-6 py-3 bg-indigo-600 text-white font-bold rounded-xl hover:bg-indigo-700 transition-colors">
                    Return to Map
                </Link>
            </div>
        );
    }

    // Prepare chart data - group by timestamp
    const chartData = history.map((item) => ({
        time: new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        generation: ['grid_export', 'p2p_sell'].includes(item.type) ? item.amount_kwh : 0,
        consumption: ['grid_purchase', 'p2p_buy'].includes(item.type) ? item.amount_kwh : 0,
        isP2P: item.is_p2p,
        type: item.type
    }));

    // Pie chart for energy breakdown
    const breakdownData = [
        { name: 'Grid', value: stats?.total_cons_kwh ? Math.max(0, stats.total_cons_kwh - (history.filter(h => h.is_p2p && h.type === 'p2p_buy').reduce((acc, curr) => acc + curr.amount_kwh, 0))) : 0, color: '#f43f5e' },
        { name: 'P2P Purchase', value: history.filter(h => h.type === 'p2p_buy').reduce((acc, curr) => acc + curr.amount_kwh, 0), color: '#6366f1' },
        { name: 'Solar Self', value: stats?.total_solar_self_kwh || 0, color: '#f59e0b' },
    ].filter(d => d.value > 0);

    return (
        <div className="min-h-screen bg-slate-950 text-slate-200">
            <div className="max-w-7xl mx-auto p-6 space-y-8 animate-in fade-in duration-500">
                {/* Header */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                    <div className="space-y-2">
                        <div className="flex items-center gap-3">
                            <Link href="/map" className="p-2 hover:bg-white/5 rounded-xl transition-colors text-slate-400 hover:text-white">
                                <ChevronLeft className="w-6 h-6" />
                            </Link>
                            <h1 className="text-4xl font-black tracking-tighter text-white uppercase">{metadata.location_name}</h1>
                        </div>
                        <div className="flex items-center gap-4 pl-14">
                            <div className="flex items-center gap-1.5 text-xs font-bold text-slate-500 uppercase tracking-widest">
                                <Activity className="w-3.5 h-3.5" />
                                {metadata.meter_id}
                            </div>
                            <div className="h-4 w-px bg-white/10" />
                            <div className="flex items-center gap-1.5 text-xs font-bold text-slate-500 uppercase tracking-widest">
                                <MapPin className="w-3.5 h-3.5" />
                                {metadata.latitude.toFixed(4)}, {metadata.longitude.toFixed(4)}
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className={`px-4 py-2 rounded-xl border font-black text-xs uppercase tracking-widest ${
                            metadata.meter_type === 'prosumer' ? 'bg-amber-500/10 border-amber-500/20 text-amber-400' : 'bg-blue-500/10 border-blue-500/20 text-blue-400'
                        }`}>
                            {metadata.meter_type}
                        </div>
                        <div className="px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl font-black text-xs text-emerald-400 uppercase tracking-widest">
                            Active
                        </div>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <StatCard 
                        title="Current Generation"
                        value={history.find(h => ['grid_export', 'p2p_sell'].includes(h.type))?.amount_kwh.toFixed(2) || "0.00"}
                        unit="kWh"
                        icon={<Sun className="w-5 h-5 text-amber-400" />}
                        status="neutral"
                        trend="Live"
                        trendLabel="Solar"
                    />
                    <StatCard 
                        title="Current Consumption"
                        value={history.find(h => ['grid_purchase', 'p2p_buy'].includes(h.type))?.amount_kwh.toFixed(2) || "0.00"}
                        unit="kWh"
                        icon={<Zap className="w-5 h-5 text-rose-400" />}
                        status="neutral"
                        trend="Live"
                        trendLabel="Load"
                    />
                    <StatCard 
                        title="Total Session Gen"
                        value={stats?.total_gen_kwh.toFixed(2) || "0.00"}
                        unit="kWh"
                        icon={<ArrowUpRight className="w-5 h-5 text-emerald-400" />}
                        status="success"
                        trend="Accumulated"
                        trendLabel="Today"
                    />
                    <StatCard 
                        title="Total Session Cons"
                        value={stats?.total_cons_kwh.toFixed(2) || "0.00"}
                        unit="kWh"
                        icon={<ArrowDownRight className="w-5 h-5 text-rose-400" />}
                        status="warning"
                        trend="Accumulated"
                        trendLabel="Today"
                    />
                    <StatCard 
                        title="Total Revenue"
                        value={stats?.total_revenue_baht.toFixed(2) || "0.00"}
                        unit="฿"
                        icon={<Coins className="w-5 h-5 text-indigo-400" />}
                        status="success"
                        trend={stats?.net_financial_baht && stats.net_financial_baht > 0 ? "Profit" : "Revenue"}
                        trendLabel="Total"
                    />
                    <StatCard 
                        title="Total Cost"
                        value={stats?.total_cost_baht.toFixed(2) || "0.00"}
                        unit="฿"
                        icon={<CreditCard className="w-5 h-5 text-rose-400" />}
                        status="error"
                        trend="Expenses"
                        trendLabel="Total"
                    />
                    <StatCard 
                        title="Net Performance"
                        value={(stats?.net_financial_baht || 0).toFixed(2)}
                        unit="฿"
                        icon={<TrendingUp className="w-5 h-5 text-emerald-400" />}
                        status={(stats?.net_financial_baht || 0) >= 0 ? 'success' : 'error'}
                        trend={(stats?.net_financial_baht || 0) >= 0 ? "SURPLUS" : "DEFICIT"}
                        trendLabel="Result"
                    />
                </div>

                {/* Main Content Area */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <div className="lg:col-span-2 space-y-8">
                        {/* History Chart */}
                        <div className="glass rounded-3xl p-8 border border-white/5 space-y-6">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-black text-white uppercase tracking-tight flex items-center gap-2">
                                    <History className="w-5 h-5 text-indigo-400" />
                                    Energy History
                                </h3>
                                <div className="flex gap-4">
                                    <div className="flex items-center gap-2">
                                        <div className="w-3 h-3 bg-amber-500 rounded-full" />
                                        <span className="text-[10px] font-bold text-slate-500 uppercase">Gen</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="w-3 h-3 bg-rose-500 rounded-full" />
                                        <span className="text-[10px] font-bold text-slate-500 uppercase">Cons</span>
                                    </div>
                                </div>
                            </div>

                            <div className="h-[400px] w-full mt-4">
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={chartData}>
                                        <defs>
                                            <linearGradient id="colorGen" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                                                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                                            </linearGradient>
                                            <linearGradient id="colorCons" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3} />
                                                <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                                        <XAxis dataKey="time" stroke="#475569" fontSize={10} fontWeight="bold" tickLine={false} axisLine={false} />
                                        <YAxis stroke="#475569" fontSize={10} fontWeight="bold" tickLine={false} axisLine={false} />
                                        <Tooltip 
                                            contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '16px' }}
                                            labelStyle={{ color: '#94a3b8', fontWeight: 'bold', marginBottom: '4px' }}
                                        />
                                        <Area type="monotone" dataKey="generation" stroke="#f59e0b" fillOpacity={1} fill="url(#colorGen)" strokeWidth={3} />
                                        <Area type="monotone" dataKey="consumption" stroke="#f43f5e" fillOpacity={1} fill="url(#colorCons)" strokeWidth={3} />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        {/* Recent Trades Table */}
                        <div className="glass rounded-3xl p-8 border border-white/5 space-y-6">
                            <h3 className="text-lg font-black text-white uppercase tracking-tight flex items-center gap-2">
                                <Activity className="w-5 h-5 text-indigo-400" />
                                Market Activity (P2P Trades)
                            </h3>
                            <div className="overflow-x-auto">
                                <table className="w-full text-left">
                                    <thead>
                                        <tr className="border-b border-white/5">
                                            <th className="pb-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">Time</th>
                                            <th className="pb-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">Type</th>
                                            <th className="pb-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">Counterparty</th>
                                            <th className="pb-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">Energy</th>
                                            <th className="pb-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">Price</th>
                                            <th className="pb-4 text-[10px] font-black text-slate-500 uppercase tracking-widest text-right">Total</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-white/5">
                                        {history.filter(h => h.is_p2p).map((trade, index) => (
                                            <tr key={index} className="hover:bg-white/5 transition-colors">
                                                <td className="py-4 text-xs font-bold text-slate-400">{new Date(trade.timestamp).toLocaleTimeString()}</td>
                                                <td className="py-4">
                                                    <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase ${
                                                        trade.type === 'p2p_sell' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-indigo-500/10 text-indigo-400'
                                                    }`}>
                                                        {trade.type === 'p2p_sell' ? 'Sale' : 'Purchase'}
                                                    </span>
                                                </td>
                                                <td className="py-4 text-xs font-mono text-slate-300">{trade.counterparty || 'Market'}</td>
                                                <td className="py-4 text-xs font-black text-white">{trade.amount_kwh.toFixed(2)} kWh</td>
                                                <td className="py-4 text-xs font-bold text-slate-400">{trade.price.toFixed(2)} ฿</td>
                                                <td className="py-4 text-xs font-black text-white text-right">{trade.total.toFixed(2)} ฿</td>
                                            </tr>
                                        ))}
                                        {history.filter(h => h.is_p2p).length === 0 && (
                                            <tr>
                                                <td colSpan={6} className="py-8 text-center text-xs font-bold text-slate-500 uppercase tracking-widest">
                                                    No P2P trades recorded in this session
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    <div className="space-y-8">
                        {/* Digital Wallet */}
                        <div className="glass rounded-3xl p-8 border border-white/5 space-y-6">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-black text-white uppercase tracking-tight flex items-center gap-2">
                                    <Wallet className="w-5 h-5 text-emerald-400" />
                                    Digital Wallet
                                </h3>
                                {wallet?.is_synced_with_solana && (
                                    <div className="flex items-center gap-1.5 px-2 py-1 bg-indigo-500/10 border border-indigo-500/20 rounded-lg">
                                        <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-pulse" />
                                        <span className="text-[10px] font-black text-indigo-400 uppercase">Synced</span>
                                    </div>
                                )}
                            </div>
                            
                            <div className="space-y-4">
                                {/* THB Balance */}
                                <div className="p-4 rounded-2xl bg-white/5 border border-white/5 flex items-center justify-between group overflow-hidden relative">
                                    <div className="absolute top-0 right-0 p-2 opacity-5 translate-x-1/4 -translate-y-1/4 group-hover:opacity-10 transition-opacity">
                                        <Globe className="w-16 h-16 text-white" />
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Thai Baht (Fiat)</p>
                                        <p className="text-xl font-black text-white">฿ {wallet?.balances.thb.toLocaleString() || "0.00"}</p>
                                    </div>
                                    <RefreshCw className="w-4 h-4 text-slate-500 group-hover:text-amber-400 transition-colors" />
                                </div>

                                {/* SOL Balance */}
                                <div className="p-4 rounded-2xl bg-indigo-500/5 border border-indigo-500/10 flex items-center justify-between group overflow-hidden relative">
                                    <div className="absolute top-0 right-0 p-2 opacity-5 translate-x-1/4 -translate-y-1/4 group-hover:opacity-10 transition-opacity">
                                        <Cpu className="w-16 h-16 text-white" />
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-black text-indigo-400/60 uppercase tracking-widest">Solana (Gas)</p>
                                        <div className="flex items-baseline gap-2">
                                            <p className="text-xl font-black text-white">{wallet?.balances.sol.toFixed(4) || "0.0000"} SOL</p>
                                            {wallet?.onchain_sol !== undefined && (
                                                <p className="text-[10px] font-bold text-indigo-400/60">On-chain: {wallet.onchain_sol.toFixed(4)}</p>
                                            )}
                                        </div>
                                    </div>
                                    <button 
                                        onClick={handleAirdrop}
                                        className="p-1 px-2 text-[8px] font-black bg-indigo-500/20 text-indigo-300 rounded hover:bg-indigo-500/40 transition-colors uppercase tracking-tight z-10"
                                    >
                                        Airdrop
                                    </button>
                                </div>

                                {/* GTNX Balance */}
                                <div className="p-4 rounded-2xl bg-emerald-500/5 border border-emerald-500/10 flex items-center justify-between group overflow-hidden relative">
                                    <div className="absolute top-0 right-0 p-2 opacity-5 translate-x-1/4 -translate-y-1/4 group-hover:opacity-10 transition-opacity">
                                        <Coins className="w-16 h-16 text-white" />
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-black text-emerald-400/60 uppercase tracking-widest">GridTokenX (Green)</p>
                                        <div className="flex items-baseline gap-2">
                                            <p className="text-xl font-black text-emerald-400">{wallet?.balances.gtnx.toFixed(2) || "0.0"}</p>
                                            {wallet?.onchain_grx !== undefined && (
                                                <p className="text-[10px] font-bold text-emerald-400/60">On-chain: {wallet.onchain_grx.toFixed(2)}</p>
                                            )}
                                        </div>
                                    </div>
                                    {wallet?.is_synced_with_solana ? (
                                        <div className="flex items-center gap-1 bg-emerald-500/20 px-2 py-0.5 rounded text-[8px] font-black text-emerald-300 uppercase">
                                            On-Chain
                                        </div>
                                    ) : (
                                        <div className="flex items-center gap-1 bg-amber-500/20 px-2 py-0.5 rounded text-[8px] font-black text-amber-300 uppercase">
                                            Local
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div className="pt-6 border-t border-white/5 space-y-4">
                                <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-widest text-slate-500">
                                    <span>Green Rewards Progress</span>
                                    <span className="text-emerald-400">{(wallet?.stats.green_rewards_earned || 0).toFixed(1)} / 500 kWh</span>
                                </div>
                                <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                                    <div 
                                        className="bg-emerald-500 h-full transition-all duration-1000" 
                                        style={{ width: `${Math.min(100, ((wallet?.stats.green_rewards_earned || 0) / 500) * 100)}%` }} 
                                    />
                                </div>
                                <p className="text-[8px] text-slate-500 font-bold leading-relaxed italic">
                                    * GTNX tokens are minted automatically based on real-time solar generation verified by the Oracle Bridge.
                                </p>
                            </div>
                        </div>

                        {/* Pie Chart Card */}
                        <div className="glass rounded-3xl p-8 border border-white/5 space-y-6 overflow-hidden">
                            <h3 className="text-sm font-black text-white uppercase tracking-tight flex items-center gap-2">
                                <Activity className="w-4 h-4 text-indigo-400" />
                                Energy Mix
                            </h3>
                            <div className="py-2 flex items-center justify-center">
                                <div className="h-[160px] w-full">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie
                                                data={breakdownData}
                                                cx="50%"
                                                cy="50%"
                                                innerRadius={60}
                                                outerRadius={80}
                                                paddingAngle={5}
                                                dataKey="value"
                                            >
                                                {breakdownData.map((entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                                ))}
                                            </Pie>
                                            <Tooltip 
                                                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                                                itemStyle={{ fontSize: '10px', fontWeight: 'bold' }}
                                            />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                                {breakdownData.map((d, i) => (
                                    <div key={i} className="flex items-center gap-2">
                                        <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: d.color }} />
                                        <span className="text-[10px] font-bold text-slate-500 uppercase">{d.name}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Billing Summary */}
                        <div className="glass rounded-3xl p-8 border border-white/5 space-y-6">
                            <h3 className="text-lg font-black text-white uppercase tracking-tight flex items-center gap-2">
                                <CreditCard className="w-5 h-5 text-emerald-400" />
                                Billing History
                            </h3>
                            <div className="space-y-4">
                                {billing.length > 0 ? billing.map((bill) => (
                                    <div key={`${bill.month}-${bill.year}`} className="p-4 bg-white/5 rounded-2xl border border-white/5 hover:bg-white/10 transition-colors cursor-pointer group">
                                        <div className="flex justify-between items-center">
                                            <div>
                                                <div className="text-[10px] font-black text-indigo-400 uppercase">
                                                    {new Date(bill.year, bill.month - 1).toLocaleString('default', { month: 'long', year: 'numeric' })}
                                                </div>
                                                <div className="text-lg font-black text-white group-hover:text-emerald-400 transition-colors">
                                                    {bill.net_amount.toFixed(2)} ฿
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <div className="text-[10px] font-bold text-slate-500 uppercase tracking-tight">Carbon Saved</div>
                                                <div className="text-sm font-black text-emerald-500">{bill.carbon_saved.toFixed(1)} kg</div>
                                            </div>
                                        </div>
                                    </div>
                                )) : (
                                    <div className="py-8 text-center text-[10px] font-bold text-slate-500 uppercase tracking-widest bg-white/5 rounded-2xl border border-dashed border-white/10">
                                        No billing data available
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MeterDetails;
