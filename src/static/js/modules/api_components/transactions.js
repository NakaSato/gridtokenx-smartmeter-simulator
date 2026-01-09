import { showStatusMessage, updateTransactionTable } from '../ui.js';

const API_BASE = window.location.origin;

export async function testP2PTransaction(buyerZone, sellerZone, amount) {
    try {
        showStatusMessage('Validating P2P Transaction...', 'info');
        const response = await fetch(`${API_BASE}/api/v1/p2p/calculate-cost`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                buyer_zone_id: parseInt(buyerZone),
                seller_zone_id: parseInt(sellerZone),
                energy_amount: parseFloat(amount)
            })
        });
        const data = await response.json();
        return data; // Returns TransactionCost with compliance info
    } catch (e) {
        console.error('Error testing P2P transaction:', e);
        showStatusMessage('Error testing P2P transaction', 'error');
        throw e;
    }
}

export async function fetchTransactions() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/p2p/transactions?limit=20`);
        if (response.ok) {
            const transactions = await response.json();
            updateTransactionTable(transactions);
        }
    } catch (e) {
        console.error('Error fetching transactions:', e);
    }
}
