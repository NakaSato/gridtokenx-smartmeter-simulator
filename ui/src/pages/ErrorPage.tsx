import { Link, useRouteError } from 'react-router-dom';
import { Zap, Home, AlertTriangle, ServerCrash, ArrowLeft } from 'lucide-react';

interface ErrorPageProps {
    status?: number;
    title?: string;
    message?: string;
}

export const NotFoundPage: React.FC<ErrorPageProps> = ({
    status = 404,
    title = 'Page Not Found',
    message = "Sorry, the page you're looking for doesn't exist."
}) => {
    return (
        <div className="min-h-screen w-full flex items-center justify-center bg-slate-950 text-white relative overflow-hidden">
            {/* Background Grid Pattern */}
            <div className="absolute inset-0 opacity-20">
                <div className="absolute inset-0" style={{
                    backgroundImage: 'linear-gradient(rgba(99, 102, 241, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(99, 102, 241, 0.1) 1px, transparent 1px)',
                    backgroundSize: '50px 50px'
                }} />
            </div>

            {/* Animated Glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl animate-pulse" />

            <div className="relative z-10 text-center px-6 max-w-2xl">
                {/* Status Code */}
                <div className="mb-8">
                    <h1 className="text-9xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 animate-pulse">
                        {status}
                    </h1>
                </div>

                {/* Icon */}
                <div className="mb-6 flex justify-center">
                    <div className="p-4 bg-indigo-500/20 rounded-3xl border border-indigo-500/30">
                        <Home className="w-16 h-16 text-indigo-400" />
                    </div>
                </div>

                {/* Title */}
                <h2 className="text-3xl font-black text-white mb-4">
                    {title}
                </h2>

                {/* Message */}
                <p className="text-slate-400 text-lg mb-8 leading-relaxed">
                    {message}
                </p>

                {/* Actions */}
                <div className="flex items-center justify-center gap-4">
                    <Link
                        to="/dashboard"
                        className="px-8 py-4 bg-indigo-500 hover:bg-indigo-400 text-white text-sm font-black rounded-2xl transition-all shadow-lg shadow-indigo-500/30 hover:shadow-indigo-500/50 flex items-center gap-2"
                    >
                        <Home className="w-4 h-4" />
                        Back to Dashboard
                    </Link>
                    <Link
                        to="/"
                        className="px-8 py-4 glass hover:bg-white/10 text-white text-sm font-black rounded-2xl transition-all border border-white/10 flex items-center gap-2"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Go Home
                    </Link>
                </div>

                {/* Quick Links */}
                <div className="mt-12 pt-8 border-t border-white/10">
                    <p className="text-xs text-slate-500 uppercase tracking-widest font-bold mb-4">
                        Popular Pages
                    </p>
                    <div className="flex items-center justify-center gap-6 text-sm">
                        <Link to="/grid-map" className="text-slate-400 hover:text-indigo-400 transition-colors font-medium">
                            Grid Map
                        </Link>
                        <Link to="/3d-map" className="text-slate-400 hover:text-indigo-400 transition-colors font-medium">
                            3D View
                        </Link>
                        <Link to="/topology" className="text-slate-400 hover:text-indigo-400 transition-colors font-medium">
                            Topology
                        </Link>
                        <Link to="/vpp" className="text-slate-400 hover:text-indigo-400 transition-colors font-medium">
                            VPP
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
};

export const ServerErrorPage: React.FC<ErrorPageProps> = ({
    status = 500,
    title = 'Server Error',
    message = "Something went wrong. Our team has been notified and we're working on it."
}) => {
    return (
        <div className="min-h-screen w-full flex items-center justify-center bg-slate-950 text-white relative overflow-hidden">
            {/* Background Grid Pattern */}
            <div className="absolute inset-0 opacity-20">
                <div className="absolute inset-0" style={{
                    backgroundImage: 'linear-gradient(rgba(239, 68, 68, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(239, 68, 68, 0.1) 1px, transparent 1px)',
                    backgroundSize: '50px 50px'
                }} />
            </div>

            {/* Animated Glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-rose-500/20 rounded-full blur-3xl animate-pulse" />

            <div className="relative z-10 text-center px-6 max-w-2xl">
                {/* Status Code */}
                <div className="mb-8">
                    <h1 className="text-9xl font-black text-transparent bg-clip-text bg-gradient-to-r from-rose-400 via-orange-400 to-yellow-400 animate-pulse">
                        {status}
                    </h1>
                </div>

                {/* Icon */}
                <div className="mb-6 flex justify-center">
                    <div className="p-4 bg-rose-500/20 rounded-3xl border border-rose-500/30">
                        <ServerCrash className="w-16 h-16 text-rose-400" />
                    </div>
                </div>

                {/* Title */}
                <h2 className="text-3xl font-black text-white mb-4">
                    {title}
                </h2>

                {/* Message */}
                <p className="text-slate-400 text-lg mb-8 leading-relaxed">
                    {message}
                </p>

                {/* Actions */}
                <div className="flex items-center justify-center gap-4">
                    <Link
                        to="/dashboard"
                        className="px-8 py-4 bg-rose-500 hover:bg-rose-400 text-white text-sm font-black rounded-2xl transition-all shadow-lg shadow-rose-500/30 hover:shadow-rose-500/50 flex items-center gap-2"
                    >
                        <Home className="w-4 h-4" />
                        Back to Dashboard
                    </Link>
                    <button
                        onClick={() => window.location.reload()}
                        className="px-8 py-4 glass hover:bg-white/10 text-white text-sm font-black rounded-2xl transition-all border border-white/10 flex items-center gap-2"
                    >
                        <Zap className="w-4 h-4" />
                        Try Again
                    </button>
                </div>

                {/* Help Info */}
                <div className="mt-12 pt-8 border-t border-white/10">
                    <div className="flex items-start gap-4 p-4 bg-amber-500/10 rounded-2xl border border-amber-500/20 max-w-md mx-auto">
                        <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                        <div className="text-left">
                            <p className="text-xs text-amber-200 font-medium mb-1">
                                Having trouble?
                            </p>
                            <p className="text-[10px] text-amber-300/70">
                                Try clearing your browser cache or contact support if the issue persists.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Error boundary component for route errors
export const RouteErrorBoundary: React.FC = () => {
    const error = useRouteError() as any;
    
    const isServerError = error?.status >= 500;
    
    return isServerError ? (
        <ServerErrorPage
            status={error?.status || 500}
            title={error?.statusText || 'Server Error'}
            message={error?.data?.message || "An unexpected error occurred."}
        />
    ) : (
        <NotFoundPage
            status={error?.status || 404}
            title={error?.statusText || 'Not Found'}
            message={error?.data?.message || "The page you're looking for doesn't exist."}
        />
    );
};
