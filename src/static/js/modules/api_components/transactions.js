import { showStatusMessage } from '../ui.js';

export async function testP2PTransaction(buyerZone, sellerZone, amount) {
    console.log('P2P transaction endpoint not available');
    showStatusMessage('P2P transactions are currently disabled', 'error');
    return null;
}

export async function fetchTransactions() {
    console.log('Transactions endpoint not available');
}
