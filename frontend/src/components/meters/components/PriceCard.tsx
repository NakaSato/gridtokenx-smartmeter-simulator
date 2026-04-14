import { Zap, TrendingUp, TrendingDown, Coins } from 'lucide-react';
import type { PriceCompareResponse } from '@/lib/types';

interface PriceComparisonDisplayProps {
    data: PriceCompareResponse;
    energyKwh: number;
}

export const PriceComparisonDisplay = ({ data, energyKwh }: PriceComparisonDisplayProps) => {
    const savings = data.analysis.buyer_savings_baht;
    const savingsPercentage = data.analysis.buyer_savings_percent;
    const isBeneficial = data.analysis.is_p2p_beneficial;

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Utility Price */}
            <div className="p-6 rounded-2xl border border-slate-500/20 bg-slate-500/10 backdrop-blur-sm">
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 rounded-lg bg-slate-500/20">
                        <Zap className="w-5 h-5 text-slate-400" />
                    </div>
                    <div>
                        <div className="text-xs font-bold text-slate-500 uppercase">Utility</div>
                        <div className="text-sm font-medium text-slate-300">{data.utility.provider}</div>
                    </div>
                </div>
                <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                        <span className="text-slate-400">Energy Charge</span>
                        <span className="text-white font-mono">{data.utility.energy_charge_baht.toFixed(2)} ฿</span>
                    </div>
                    <div className="flex justify-between text-sm">
                        <span className="text-slate-400">FT Charge</span>
                        <span className="text-white font-mono">{data.utility.ft_charge_baht.toFixed(2)} ฿</span>
                    </div>
                    <div className="flex justify-between text-sm">
                        <span className="text-slate-400">Service Charge</span>
                        <span className="text-white font-mono">{data.utility.service_charge_baht.toFixed(2)} ฿</span>
                    </div>
                    <div className="flex justify-between text-sm">
                        <span className="text-slate-400">VAT</span>
                        <span className="text-white font-mono">{data.utility.vat_baht.toFixed(2)} ฿</span>
                    </div>
                    <div className="pt-2 border-t border-slate-500/20">
                        <div className="flex justify-between">
                            <span className="text-slate-300 font-bold">Total</span>
                            <span className="text-white font-black text-lg">{data.utility.total_amount_baht.toFixed(2)} ฿</span>
                        </div>
                        <div className="text-xs text-slate-500 mt-1">
                            {data.utility.average_rate_baht_kwh.toFixed(3)} ฿/kWh
                        </div>
                    </div>
                </div>
            </div>

            {/* P2P Price */}
            <div className="p-6 rounded-2xl border border-emerald-500/20 bg-emerald-500/10 backdrop-blur-sm">
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 rounded-lg bg-emerald-500/20">
                        <Coins className="w-5 h-5 text-emerald-400" />
                    </div>
                    <div>
                        <div className="text-xs font-bold text-emerald-500 uppercase">P2P Trading</div>
                        <div className="text-sm font-medium text-emerald-300">Peer-to-Peer</div>
                    </div>
                </div>
                <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                        <span className="text-emerald-300">Energy Cost</span>
                        <span className="text-white font-mono">{data.p2p.energy_cost_baht.toFixed(2)} ฿</span>
                    </div>
                    <div className="flex justify-between text-sm">
                        <span className="text-emerald-300">Wheeling Cost</span>
                        <span className="text-white font-mono">{data.p2p.wheeling_charge_baht.toFixed(2)} ฿</span>
                    </div>
                    <div className="flex justify-between text-sm">
                        <span className="text-emerald-300">MCP</span>
                        <span className="text-white font-mono">{data.p2p.market_clearing_price_baht_kwh.toFixed(4)} ฿/kWh</span>
                    </div>
                    <div className="pt-2 border-t border-emerald-500/20">
                        <div className="flex justify-between">
                            <span className="text-emerald-300 font-bold">Buyer Total</span>
                            <span className="text-emerald-400 font-black text-lg">{data.p2p.buyer_total_cost_baht.toFixed(2)} ฿</span>
                        </div>
                        <div className="text-xs text-emerald-500 mt-1">
                            {data.p2p.buyer_total_baht_kwh.toFixed(4)} ฿/kWh
                        </div>
                    </div>
                </div>
            </div>

            {/* Analysis */}
            <div className={`p-6 rounded-2xl border backdrop-blur-sm ${
                isBeneficial
                    ? 'border-emerald-500/20 bg-emerald-500/10'
                    : 'border-rose-500/20 bg-rose-500/10'
            }`}>
                <div className="flex items-center gap-3 mb-4">
                    <div className={`p-2 rounded-lg ${
                        isBeneficial ? 'bg-emerald-500/20' : 'bg-rose-500/20'
                    }`}>
                        {isBeneficial ? (
                            <TrendingDown className="w-5 h-5 text-emerald-400" />
                        ) : (
                            <TrendingUp className="w-5 h-5 text-rose-400" />
                        )}
                    </div>
                    <div>
                        <div className={`text-xs font-bold uppercase tracking-widest ${
                            isBeneficial ? 'text-emerald-500' : 'text-rose-500'
                        }`}>
                            {isBeneficial ? 'You Save' : 'Extra Cost'}
                        </div>
                        <div className="text-sm font-medium text-slate-300">with P2P</div>
                    </div>
                </div>
                <div className="space-y-3">
                    <div className="text-center">
                        <div className={`text-4xl font-black ${
                            isBeneficial ? 'text-emerald-400' : 'text-rose-400'
                        }`}>
                            {Math.abs(savings).toFixed(2)} ฿
                        </div>
                        <div className="text-xs text-slate-500 mt-1">
                            on {energyKwh} kWh
                        </div>
                    </div>
                    <div className={`pt-3 border-t ${
                        isBeneficial ? 'border-emerald-500/20' : 'border-rose-500/20'
                    }`}>
                        <div className="text-center">
                            <div className={`text-2xl font-black ${
                                savingsPercentage >= 0 ? 'text-emerald-400' : 'text-rose-400'
                            }`}>
                                {Math.abs(savingsPercentage).toFixed(1)}%
                            </div>
                            <div className="text-xs text-slate-500 mt-1">
                                {savingsPercentage >= 0 ? 'cheaper' : 'more expensive'} than utility
                            </div>
                        </div>
                    </div>
                </div>
                <div className={`mt-4 pt-4 border-t ${
                    isBeneficial ? 'border-emerald-500/20' : 'border-rose-500/20'
                }`}>
                    <div className="text-center text-xs font-bold">
                        <div className={isBeneficial ? 'text-emerald-400' : 'text-rose-400'}>
                            {data.recommendation}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
