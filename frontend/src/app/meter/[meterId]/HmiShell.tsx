"use client";

import { type ReactNode } from 'react';
import { useHmiTheme } from '@/components/providers/HmiThemeProvider';

// Re-export so existing imports from this module keep working.
export { useHmiTheme } from '@/components/providers/HmiThemeProvider';
export type { Theme } from '@/components/providers/HmiThemeProvider';

// Meter-detail layout classes, scoped under `.hmi`. Palette tokens + theme
// switching live globally in hmi.css; this only carries the page's structure.
const HMI_CSS = `
.hmi * { box-sizing:border-box; margin:0; padding:0; }

.hmi{ font-family:'IBM Plex Sans',sans-serif; background:var(--canvas); color:var(--txt);
      padding:4rem 16px 16px; min-height:100vh; -webkit-font-smoothing:antialiased; }
.hmi .mono{ font-family:'IBM Plex Mono',monospace; font-variant-numeric:tabular-nums; }

.hmi .hd{ display:flex; align-items:flex-start; gap:14px; border:1px solid var(--line);
     background:var(--panel); padding:12px 14px; margin-bottom:12px; }
.hmi .hd .back{ width:30px; height:30px; flex:none; display:flex; align-items:center; justify-content:center;
           background:var(--panel-2); border:1px solid var(--line-2); color:var(--txt); cursor:pointer; font-size:15px;
           text-decoration:none; }
.hmi .hd .titlewrap{ flex:1; min-width:0; }
.hmi .hd .title{ font-size:18px; font-weight:700; letter-spacing:.04em; color:var(--txt-val); }
.hmi .hd .meta{ font-size:11px; color:var(--lbl); margin-top:3px; display:flex; gap:10px; flex-wrap:wrap; }
.hmi .hd .meta .uuid{ font-family:'IBM Plex Mono'; color:var(--lbl-dim); }
.hmi .hd .badges{ display:flex; gap:7px; flex-wrap:wrap; align-items:center; }
.hmi .bdg{ font-size:10px; letter-spacing:.1em; text-transform:uppercase; padding:4px 10px;
      border:1px solid var(--line-2); color:var(--lbl); white-space:nowrap; }
.hmi .bdg.pv{ color:var(--gen); border-color:var(--warn-bd); }
.hmi .bdg.type{ color:var(--info); border-color:var(--line-2); }
.hmi .bdg.active{ color:var(--ok); border-color:var(--ok-bd); }

.hmi .kpis{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:12px; }
@media (max-width:900px){ .hmi .kpis{ grid-template-columns:repeat(2,1fr); } }
@media (max-width:520px){ .hmi .kpis{ grid-template-columns:1fr; } }
.hmi .kpi{ border:1px solid var(--line); background:var(--panel); padding:12px 13px; }
.hmi .kpi .top{ display:flex; align-items:center; justify-content:space-between; }
.hmi .kpi .lbl{ font-size:10px; letter-spacing:.14em; text-transform:uppercase; color:var(--lbl); }
.hmi .kpi .st{ font-size:9px; letter-spacing:.1em; text-transform:uppercase; padding:1px 6px; border:1px solid var(--line-2); color:var(--lbl); }
.hmi .kpi .st.ok{ color:var(--ok); border-color:var(--ok-bd); }
.hmi .kpi .st.warn{ color:var(--warn); border-color:var(--warn-bd); }
.hmi .kpi .st.alarm{ color:var(--alarm); border-color:var(--alarm-bd); background:var(--alarm-bg); }
.hmi .kpi .num{ margin:9px 0 2px; display:flex; align-items:baseline; gap:5px; }
.hmi .kpi .num .v{ font-size:30px; font-weight:500; color:var(--txt-val); line-height:1; }
.hmi .kpi .num .v.warn{ color:var(--warn); } .hmi .kpi .num .v.alarm{ color:var(--alarm); }
.hmi .kpi .num .u{ font-size:11px; color:var(--lbl); }
.hmi .kpi .bar{ position:relative; height:7px; background:var(--bar-bg); border:1px solid var(--line); margin-top:10px; }
.hmi .kpi .bar .band{ position:absolute; top:0; bottom:0; background:var(--band); }
.hmi .kpi .bar .fill{ position:absolute; top:0; bottom:0; left:0; background:var(--txt); opacity:.5; }
.hmi .kpi .bar .fill.warn{ background:var(--warn); opacity:.8; } .hmi .kpi .bar .fill.alarm{ background:var(--alarm); opacity:.85; }
.hmi .kpi .bar.bi .zero{ position:absolute; top:-3px; bottom:-3px; left:50%; width:1px; background:var(--line-2); }
.hmi .kpi .bar.bi .fill{ left:auto; }
.hmi .kpi .sub{ font-size:10px; margin-top:9px; color:var(--lbl); }
.hmi .kpi .sub b{ color:var(--ok); font-weight:600; }

.hmi .panel{ border:1px solid var(--line); background:var(--panel); margin-bottom:12px; }
.hmi .panel-hd{ display:flex; align-items:center; justify-content:space-between; gap:10px;
           padding:9px 13px; border-bottom:1px solid var(--line); background:var(--panel-2); }
.hmi .panel-hd .t{ font-size:11px; letter-spacing:.16em; text-transform:uppercase; color:var(--lbl); font-weight:600; }
.hmi .panel-hd .meta{ font-size:11px; color:var(--lbl-dim); }
.hmi .panel-bd{ padding:13px; }

.hmi .legend{ display:flex; gap:14px; }
.hmi .legend span{ display:inline-flex; align-items:center; gap:6px; font-size:10px; letter-spacing:.1em; text-transform:uppercase; color:var(--lbl); }
.hmi .legend .sw{ width:14px; height:3px; }
.hmi .legend .sw.gen{ background:var(--gen); } .hmi .legend .sw.cons{ background:var(--cons); }

.hmi .chart-wrap{ width:100%; overflow:hidden; }
.hmi svg.chart{ width:100%; height:auto; display:block; }
.hmi .chart .axis{ stroke:var(--grid); stroke-width:1; }
.hmi .chart .gl{ stroke:var(--grid); stroke-width:1; stroke-dasharray:2 4; opacity:.6; }
.hmi .chart .tk{ fill:var(--lbl-dim); font:10px 'IBM Plex Mono',monospace; }
.hmi .chart .ln-gen{ fill:none; stroke:var(--gen); stroke-width:1.8; }
.hmi .chart .ln-cons{ fill:none; stroke:var(--cons); stroke-width:1.8; }
.hmi .chart-empty{ display:flex; align-items:center; justify-content:center; height:240px;
     font-size:10px; letter-spacing:.14em; text-transform:uppercase; color:var(--lbl-dim); }

.hmi .bill{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }
@media (max-width:900px){ .hmi .bill{ grid-template-columns:repeat(2,1fr); } }
@media (max-width:520px){ .hmi .bill{ grid-template-columns:1fr; } }
.hmi .bcard{ border:1px solid var(--line); background:var(--panel); padding:12px 13px; }
.hmi .bcard .lbl{ font-size:10px; letter-spacing:.12em; text-transform:uppercase; color:var(--lbl); }
.hmi .bcard .num{ margin:9px 0 2px; display:flex; align-items:baseline; gap:5px; }
.hmi .bcard .num .v{ font-size:25px; font-weight:500; color:var(--txt-val); line-height:1; }
.hmi .bcard .num .v.ok{ color:var(--ok); } .hmi .bcard .num .v.alarm{ color:var(--alarm); }
.hmi .bcard .num .u{ font-size:11px; color:var(--lbl); }
.hmi .bcard .sub{ font-size:10px; margin-top:8px; color:var(--lbl); }
.hmi .bcard .sub b{ color:var(--txt); font-weight:600; }

.hmi .theme-sw{ display:flex; border:1px solid var(--line-2); }
.hmi .tsw{ font-size:10px; letter-spacing:.1em; text-transform:uppercase; color:var(--lbl);
      background:var(--panel-2); border:none; border-right:1px solid var(--line-2); padding:5px 9px; cursor:pointer; }
.hmi .tsw:last-child{ border-right:none; }
.hmi .tsw.active{ color:var(--txt-val); background:var(--canvas); box-shadow:inset 0 -2px 0 var(--info); }
`;

/**
 * Standard ISA-101 HMI layout shell for the meter detail route: injects the
 * scoped layout stylesheet and renders the `.hmi` canvas with the active theme
 * (driven by the app-wide {@link useHmiTheme}).
 */
export default function HmiShell({ children }: { children: ReactNode }) {
    const { theme } = useHmiTheme();
    return (
        <>
            <style dangerouslySetInnerHTML={{ __html: HMI_CSS }} />
            <div className="hmi" data-theme={theme}>
                {children}
            </div>
        </>
    );
}
