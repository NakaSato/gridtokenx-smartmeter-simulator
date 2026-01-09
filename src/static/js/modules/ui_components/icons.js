import { createIcons, icons } from 'lucide';

/**
 * Initialize Lucide icons in the DOM
 * Should be called after DOM updates that add new icons
 */
export function initLucideIcons() {
    createIcons({ icons });
}
