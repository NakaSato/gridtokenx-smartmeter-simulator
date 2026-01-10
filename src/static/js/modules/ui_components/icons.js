import { createIcons } from 'lucide';
// Selectively import only the icons used in the application
// This reduces bundle size from ~600KB to ~20KB for lucide
import {
    Play,
    Square,
    Pause,
    RotateCcw,
    Map,
    Plus,
    Wifi,
    Sun,
    Activity,
    Zap,
    TrendingUp,
    Users,
    Download,
    Search,
    ChevronDown,
    Loader2,
    X,
    AlertCircle,
    CheckCircle,
    Info,
    Settings,
    RefreshCw,
    Battery,
    BatteryCharging,
    Gauge,
    Power,
    Thermometer,
    Wind,
    Cloud,
    CloudRain,
} from 'lucide';

// Create an icons object with the imported icons
const icons = {
    Play,
    Square,
    Pause,
    RotateCcw,
    Map,
    Plus,
    Wifi,
    Sun,
    Activity,
    Zap,
    TrendingUp,
    Users,
    Download,
    Search,
    ChevronDown,
    Loader2,
    X,
    AlertCircle,
    CheckCircle,
    Info,
    Settings,
    RefreshCw,
    Battery,
    BatteryCharging,
    Gauge,
    Power,
    Thermometer,
    Wind,
    Cloud,
    CloudRain,
};

/**
 * Initialize Lucide icons in the DOM
 * Should be called after DOM updates that add new icons
 */
export function initLucideIcons() {
    createIcons({ icons });
}

