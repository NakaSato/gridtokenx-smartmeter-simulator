import React, { useState, useEffect, useCallback } from 'react';
import { Upload, Sun, CheckCircle, MapPin, Loader2, AlertCircle, Zap, Ruler } from 'lucide-react';
import { useNetwork } from '../context/NetworkContext';
import { cn } from '../utils.ts';
import type { SolarPanel, SolarInventoryResponse } from '../types';

export function SolarDetection() {
  const { getApiUrl } = useNetwork();
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [inventory, setInventory] = useState<SolarPanel[]>([]);
  const [mapping, setMapping] = useState<Record<string, number>>({});
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<string>('');

  const fetchInventory = useCallback(async () => {
    try {
      const res = await fetch(getApiUrl('/api/geo-sam/inventory'));
      const data: SolarInventoryResponse = await res.json();
      if (data.success) {
        setInventory(data.inventory || []);
        setMapping(data.mapping || {});
      }
    } catch (err) {
      console.error('Failed to fetch solar inventory:', err);
    }
  }, [getApiUrl]);

  useEffect(() => {
    fetchInventory();
  }, [fetchInventory]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);
    setUploadProgress('Uploading image and running Geo-SAM AI...');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(getApiUrl('/api/geo-sam/detect'), {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (data.success) {
        setUploadProgress('Updating grid state...');
        await fetchInventory();
        setFile(null);
        setUploadProgress('');
      } else {
        setError(data.message || 'Detection failed');
        setUploadProgress('');
      }
    } catch (err) {
      setError('Upload failed. Check server connection.');
      setUploadProgress('');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="glass rounded-3xl p-6 bg-gradient-to-br from-slate-900/50 to-transparent border-white/5 space-y-6 hover:border-white/10 transition-all">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Sun className="w-5 h-5 text-amber-400" />
          <h3 className="text-sm font-black uppercase tracking-widest text-slate-400">Geo-SAM Solar Inventory</h3>
        </div>
        <div className="px-3 py-1 bg-amber-500/10 text-amber-400 rounded-full text-[10px] font-black uppercase tracking-widest">
          {inventory.length} Panels Detected
        </div>
      </div>

      {/* Upload Area */}
      <div className="bg-slate-950/40 border-2 border-dashed border-white/5 rounded-2xl p-6 text-center space-y-4 hover:border-indigo-500/20 transition-all">
        {!isUploading ? (
          <>
            <div className="flex flex-col items-center gap-2">
              <Upload className="w-8 h-8 text-slate-600" />
              <p className="text-xs text-slate-400 font-medium">
                {file ? file.name : 'Upload high-res TIF for Solar Detection'}
              </p>
            </div>
            <div className="flex gap-2 justify-center">
              <label className="cursor-pointer bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded-xl text-xs font-bold text-white transition-colors">
                Select File
                <input type="file" accept=".tif,.tiff" className="hidden" onChange={handleFileChange} />
              </label>
              {file && (
                <button
                  onClick={handleUpload}
                  className="bg-indigo-500 hover:bg-indigo-400 px-4 py-2 rounded-xl text-xs font-bold text-white transition-colors shadow-lg shadow-indigo-500/20"
                >
                  Start AI Detection
                </button>
              )}
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center gap-3 py-4">
            <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
            <p className="text-xs text-indigo-400 font-black uppercase tracking-widest animate-pulse">
              {uploadProgress}
            </p>
          </div>
        )}
        {error && (
          <div className="flex items-center justify-center gap-2 text-rose-400 text-[10px] font-bold">
            <AlertCircle className="w-3 h-3" />
            {error}
          </div>
        )}
      </div>

      {/* Results Table */}
      {inventory.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-2">Detailed Inventory</h4>
          <div className="max-h-[200px] overflow-y-auto pr-2 custom-scrollbar space-y-2">
            {inventory.map((panel) => {
              // Find if this panel is matched (heuristic check: mapping usually keyed by bus index as string in JSON)
              const isMatched = Object.values(mapping).some(v => v > 0); // Simplified check
              return (
                <div key={panel.id} className="bg-slate-900/60 p-3 rounded-xl border border-white/5 flex items-center justify-between group hover:border-white/10 transition-all">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-amber-500/10 rounded-lg text-amber-400">
                      <Zap className="w-3 h-3" />
                    </div>
                    <div>
                      <div className="text-[11px] font-bold text-white flex items-center gap-2">
                        ID: {panel.id}
                        <span className="text-[9px] text-slate-500 font-mono">({panel.kwp_potential.toFixed(2)} kWp)</span>
                      </div>
                      <div className="flex items-center gap-3 mt-1">
                        <div className="flex items-center gap-1 text-[9px] text-slate-500">
                          <Ruler className="w-2.5 h-2.5" />
                          {panel.area_sqm.toFixed(1)} m²
                        </div>
                        <div className="flex items-center gap-1 text-[9px] text-slate-500">
                          <MapPin className="w-2.5 h-2.5" />
                          {panel.geometry.type}
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={cn(
                      "flex items-center gap-1.5 px-2 py-1 rounded-md text-[8px] font-black uppercase tracking-tighter",
                      isMatched
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        : "bg-slate-500/10 text-slate-500 border border-white/5"
                    )}>
                      <CheckCircle className={cn("w-2.5 h-2.5", !isMatched && "opacity-20")} />
                      {isMatched ? 'Grid Matched' : 'Pending Match'}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {inventory.length === 0 && !isUploading && (
        <div className="text-center py-6">
          <p className="text-[10px] font-bold text-slate-600 uppercase tracking-widest">
            No persistent solar inventory found
          </p>
        </div>
      )}
    </div>
  );
}
