import { memo } from 'react';
import { Link } from 'react-router-dom';
import { cn } from '../../utils';
import type { ElementType } from 'react';

interface NavLinkProps {
    to: string;
    icon: ElementType;
    label: string;
    title: string;
    color: 'emerald' | 'indigo' | 'rose' | 'amber';
}

export const NavLink = memo(({ to, icon: Icon, label, title, color }: NavLinkProps) => (
    <Link
        to={to}
        className="glass px-5 py-3.5 rounded-2xl flex items-center gap-4 hover:bg-white/5 border-white/5 hover:border-white/10 transition-all group flex-1"
    >
        <div className={cn(
            "p-2 rounded-xl transition-all group-hover:scale-110",
            color === "emerald" && "bg-emerald-500/10 text-emerald-400 group-hover:bg-emerald-500/20",
            color === "indigo" && "bg-indigo-500/10 text-indigo-400 group-hover:bg-indigo-500/20",
            color === "rose" && "bg-rose-500/10 text-rose-400 group-hover:bg-rose-500/20",
            color === "amber" && "bg-amber-500/10 text-amber-400 group-hover:bg-amber-500/20",
        )}>
            <Icon className="w-5 h-5" />
        </div>
        <div className="flex flex-col">
            <span className="text-[9px] font-black uppercase tracking-widest text-slate-500 leading-none mb-1">{label}</span>
            <span className="text-sm font-black text-white group-hover:text-indigo-200 transition-colors leading-none">{title}</span>
        </div>
    </Link>
));

NavLink.displayName = 'NavLink';
