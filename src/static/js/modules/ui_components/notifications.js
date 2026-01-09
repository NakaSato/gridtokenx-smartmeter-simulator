// Status Message
export function showStatusMessage(message, type = 'info') {
    const messageEl = document.getElementById('status-message');
    const textEl = document.getElementById('status-message-text');
    const colors = {
        'success': 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
        'error': 'bg-red-500/20 text-red-400 border border-red-500/30',
        'warning': 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
        'info': 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
    };

    // Reset classes
    messageEl.className = `hidden ml-auto flex items-center gap-3 px-3 py-1 rounded-lg text-sm transition-all`;

    // Add new classes
    messageEl.classList.add(...colors[type].split(' '));
    messageEl.classList.remove('hidden');

    if (textEl) textEl.textContent = message;

    // Auto-hide after 5 seconds
    setTimeout(() => {
        messageEl.classList.add('hidden');
    }, 5000);
}
