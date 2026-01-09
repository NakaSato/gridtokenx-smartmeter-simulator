export function updateTransactionTable(transactions) {
    const tbody = document.getElementById('transaction-table-body');
    if (!tbody) return;

    if (!transactions || transactions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="px-6 py-4 text-center text-slate-500 italic">No transactions found</td></tr>';
        return;
    }

    tbody.innerHTML = transactions.map(tx => {
        const date = new Date(tx.timestamp * 1000);
        const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

        return `
            <tr class="hover:bg-slate-800/30 transition-colors border-b border-slate-800/50 last:border-0">
                <td class="px-6 py-3 font-mono text-slate-300">${timeStr}</td>
                <td class="px-6 py-3 font-mono text-xs text-blue-300 truncate max-w-[120px]" title="${tx.buyer}">${tx.buyer}</td>
                <td class="px-6 py-3 font-mono text-xs text-emerald-300 truncate max-w-[120px]" title="${tx.seller}">${tx.seller}</td>
                <td class="px-6 py-3 text-right font-medium text-white">${tx.amount_kwh.toFixed(2)}</td>
                <td class="px-6 py-3 text-right font-medium text-slate-300">${tx.price_per_kwh.toFixed(2)}</td>
                <td class="px-6 py-3 text-right font-bold text-amber-400">${tx.total_cost.toFixed(2)}</td>
                <td class="px-6 py-3 text-center">
                    <span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide ${tx.transaction_type === 'PeerToPeer' ? 'bg-purple-500/20 text-purple-400' : 'bg-slate-700 text-slate-400'}">
                        ${tx.transaction_type === 'PeerToPeer' ? 'P2P' : tx.transaction_type}
                    </span>
                </td>
            </tr>
        `;
    }).join('');
}
