"use client";

/**
 * Filter Panel Component - Improved
 */

import { X, Search, Filter, Zap, MapPin, Building2, ChevronDown, ChevronUp } from 'lucide-react';
import React, { useState } from 'react';
import type { FilterState, InfrastructureType } from './types';
import { OPERATOR_INFO, INFRASTRUCTURE_LAYERS } from './types';

interface FilterPanelProps {
  filters: FilterState;
  onUpdateFilters: (updates: Partial<FilterState>) => void;
  onResetFilters: () => void;
  onClose: () => void;
  stats: any;
}

const INFRA_TYPE_LABELS: Record<InfrastructureType, string> = {
  transmission_substation: 'Transmission Substation',
  distribution_substation: 'Distribution Substation',
  transmission_tower: 'Transmission Tower',
  distribution_pole: 'Distribution Pole',
  power_plant: 'Power Plant',
  solar_farm: 'Solar Farm',
  battery_storage: 'Battery Storage',
  ev_charging_station: 'EV Charging Station',
};

interface SectionProps {
  title: string;
  icon: any;
  children: React.ReactNode;
  count?: number;
  isExpanded: boolean;
  onToggle: () => void;
}

const Section = ({
  title,
  icon: Icon,
  children,
  count,
  isExpanded,
  onToggle
}: SectionProps) => (
  <div className="border-b border-slate-700/50 last:border-b-0">
    <button
      onClick={onToggle}
      className="w-full flex items-center justify-between p-3 hover:bg-slate-700/30 transition-colors"
    >
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 text-slate-400" />
        <span className="text-sm font-semibold text-slate-200">{title}</span>
        {count !== undefined && count > 0 && (
          <span className="px-1.5 py-0.5 text-[10px] font-bold bg-indigo-500/20 text-indigo-400 rounded-full">
            {count}
          </span>
        )}
      </div>
      {isExpanded ? (
        <ChevronUp className="w-4 h-4 text-slate-500" />
      ) : (
        <ChevronDown className="w-4 h-4 text-slate-500" />
      )}
    </button>
    {isExpanded && (
      <div className="px-3 pb-3">{children}</div>
    )}
  </div>
);

export const FilterPanel = ({
  filters,
  onUpdateFilters,
  onResetFilters,
  onClose,
  stats
}: FilterPanelProps) => {
  const [expandedSections, setExpandedSections] = useState({
    operators: true,
    types: true,
    voltage: false,
    provinces: false,
    status: false,
  });

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const toggleOperator = (operator: 'EGAT' | 'MEA' | 'PEA') => {
    const current = filters.operators;
    const updated = current.includes(operator)
      ? current.filter(o => o !== operator)
      : [...current, operator];

    if (updated.length > 0) {
      onUpdateFilters({ operators: updated });
    }
  };

  const toggleType = (type: InfrastructureType) => {
    const current = filters.types;
    const updated = current.includes(type)
      ? current.filter(t => t !== type)
      : [...current, type];

    if (updated.length > 0) {
      onUpdateFilters({ types: updated });
    }
  };

  const toggleVoltage = (voltage: number) => {
    const current = filters.voltageLevels;
    const updated = current.includes(voltage)
      ? current.filter(v => v !== voltage)
      : [...current, voltage];

    onUpdateFilters({ voltageLevels: updated });
  };

  const toggleProvince = (province: string) => {
    const current = filters.provinces;
    const updated = current.includes(province)
      ? current.filter(p => p !== province)
      : [...current, province];

    onUpdateFilters({ provinces: updated });
  };

  const toggleStatus = (status: string) => {
    const current = filters.status;
    const updated = current.includes(status)
      ? current.filter(s => s !== status)
      : [...current, status];

    onUpdateFilters({ status: updated });
  };

  const selectAllTypes = () => {
    onUpdateFilters({ types: INFRASTRUCTURE_LAYERS.map(l => l.type) });
  };

  const clearAllTypes = () => {
    onUpdateFilters({ types: [] });
  };

  const selectAllOperators = () => {
    onUpdateFilters({ operators: ['EGAT', 'MEA', 'PEA'] });
  };

  const activeFilterCount = [
    filters.operators.length < 3 ? 1 : 0,
    filters.types.length < INFRASTRUCTURE_LAYERS.length ? 1 : 0,
    filters.voltageLevels.length > 0 ? 1 : 0,
    filters.provinces.length > 0 ? 1 : 0,
    filters.status.length < 1 ? 0 : filters.status.length > 0 ? 1 : 0,
    filters.searchQuery ? 1 : 0,
  ].filter(Boolean).length;

  return (
    <div className="absolute top-20 right-4 z-20 w-80 bg-slate-800/95 backdrop-blur-xl rounded-xl shadow-2xl border border-slate-700/50 max-h-[calc(100vh-12rem)] overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700/50 bg-gradient-to-r from-slate-800 to-slate-900 rounded-t-xl">
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-indigo-400" />
          <h2 className="text-base font-bold text-white">Filters</h2>
          {activeFilterCount > 0 && (
            <span className="px-2 py-0.5 text-[10px] font-bold bg-indigo-500 text-white rounded-full">
              {activeFilterCount} active
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onResetFilters}
            className="text-xs font-semibold text-slate-400 hover:text-white transition-colors px-2 py-1 rounded-md hover:bg-slate-700/50"
          >
            Reset All
          </button>
          <button
            onClick={onClose}
            className="p-1 rounded-md hover:bg-slate-700/50 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="p-3 border-b border-slate-700/50">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={filters.searchQuery}
            onChange={(e) => onUpdateFilters({ searchQuery: e.target.value })}
            placeholder="Search by name, ID, location..."
            className="w-full pl-9 pr-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all"
          />
        </div>
      </div>

      {/* Content */}
      <div className="divide-y divide-slate-700/50">
        {/* Operators */}
        <Section
          title="Operators"
          icon={Building2}
          count={filters.operators.length < 3 ? 3 - filters.operators.length : 0}
          isExpanded={expandedSections.operators}
          onToggle={() => toggleSection('operators')}
        >
          <div className="flex gap-1 mb-3">
            <button
              onClick={selectAllOperators}
              className="flex-1 text-[10px] font-semibold text-slate-400 hover:text-white py-1 rounded-md hover:bg-slate-700/50 transition-colors"
            >
              Select All
            </button>
          </div>
          <div className="space-y-1.5">
            {(['EGAT', 'MEA', 'PEA'] as const).map(operator => {
              const info = OPERATOR_INFO[operator];
              const count = stats?.byOperator?.[operator] || 0;
              const isActive = filters.operators.includes(operator);
              return (
                <label
                  key={operator}
                  className={`flex items-center justify-between p-2.5 rounded-lg cursor-pointer transition-all ${
                    isActive
                      ? 'bg-slate-700/70 ring-1 ring-slate-600/50'
                      : 'bg-slate-900/30 hover:bg-slate-700/30'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <div className={`w-4 h-4 rounded border-2 flex items-center justify-center transition-all ${
                      isActive ? 'border-indigo-500 bg-indigo-500' : 'border-slate-600'
                    }`}>
                      {isActive && (
                        <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </div>
                    <input
                      type="checkbox"
                      checked={isActive}
                      onChange={() => toggleOperator(operator)}
                      className="sr-only"
                    />
                    <span className="text-sm font-semibold text-white">{operator}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div
                      className="w-2.5 h-2.5 rounded-full"
                      style={{ backgroundColor: info.color }}
                    />
                    <span className="text-xs text-slate-400 font-mono">{count}</span>
                  </div>
                </label>
              );
            })}
          </div>
        </Section>

        {/* Infrastructure Types */}
        <Section
          title="Infrastructure Types"
          icon={Zap}
          count={filters.types.length < INFRASTRUCTURE_LAYERS.length ? INFRASTRUCTURE_LAYERS.length - filters.types.length : 0}
          isExpanded={expandedSections.types}
          onToggle={() => toggleSection('types')}
        >
          <div className="flex gap-1 mb-3">
            <button
              onClick={selectAllTypes}
              className="flex-1 text-[10px] font-semibold text-slate-400 hover:text-white py-1 rounded-md hover:bg-slate-700/50 transition-colors"
            >
              Select All
            </button>
            <button
              onClick={clearAllTypes}
              className="flex-1 text-[10px] font-semibold text-slate-400 hover:text-white py-1 rounded-md hover:bg-slate-700/50 transition-colors"
            >
              Clear All
            </button>
          </div>
          <div className="grid grid-cols-2 gap-1.5">
            {INFRASTRUCTURE_LAYERS.map(layer => {
              const isActive = filters.types.includes(layer.type);
              return (
                <button
                  key={layer.id}
                  onClick={() => toggleType(layer.type)}
                  className={`flex items-center gap-2 p-2 rounded-lg text-left transition-all text-xs ${
                    isActive
                      ? 'bg-slate-700/70 ring-1 ring-slate-600/50'
                      : 'bg-slate-900/30 hover:bg-slate-700/30'
                  }`}
                >
                  <div
                    className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                    style={{ backgroundColor: layer.color }}
                  />
                  <span className="text-slate-200 truncate capitalize">
                    {INFRA_TYPE_LABELS[layer.type] || layer.type.replace(/_/g, ' ')}
                  </span>
                </button>
              );
            })}
          </div>
        </Section>

        {/* Voltage Levels */}
        <Section
          title="Voltage Levels"
          icon={Zap}
          count={filters.voltageLevels.length > 0 ? filters.voltageLevels.length : undefined}
          isExpanded={expandedSections.voltage}
          onToggle={() => toggleSection('voltage')}
        >
          <div className="space-y-1.5">
            {([500, 230, 115, 33, 22] as const).map(voltage => {
              const count = (stats?.byVoltage as Record<string, number>)?.[`${voltage}kV`] || 0;
              const isActive = filters.voltageLevels.includes(voltage);
              if (count === 0) return null;
              return (
                <label
                  key={voltage}
                  className={`flex items-center justify-between p-2.5 rounded-lg cursor-pointer transition-all ${
                    isActive
                      ? 'bg-slate-700/70 ring-1 ring-slate-600/50'
                      : 'bg-slate-900/30 hover:bg-slate-700/30'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <div className={`w-4 h-4 rounded border-2 flex items-center justify-center transition-all ${
                      isActive ? 'border-indigo-500 bg-indigo-500' : 'border-slate-600'
                    }`}>
                      {isActive && (
                        <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </div>
                    <input
                      type="checkbox"
                      checked={isActive}
                      onChange={() => toggleVoltage(voltage)}
                      className="sr-only"
                    />
                    <span className="text-sm font-semibold text-white">{voltage} kV</span>
                  </div>
                  <span className="text-xs text-slate-400 font-mono">{count}</span>
                </label>
              );
            })}
          </div>
        </Section>

        {/* Provinces */}
        <Section
          title="Provinces"
          icon={MapPin}
          count={filters.provinces.length > 0 ? filters.provinces.length : undefined}
          isExpanded={expandedSections.provinces}
          onToggle={() => toggleSection('provinces')}
        >
          {stats?.byProvince && Object.keys(stats.byProvince).length > 0 ? (
            <div className="space-y-1.5 max-h-40 overflow-y-auto">
              {Object.entries(stats.byProvince as Record<string, number>)
                .sort(([, a], [, b]) => b - a)
                .map(([province, count]) => {
                  const isActive = filters.provinces.includes(province);
                  return (
                    <label
                      key={province}
                      className={`flex items-center justify-between p-2.5 rounded-lg cursor-pointer transition-all ${
                        isActive
                          ? 'bg-slate-700/70 ring-1 ring-slate-600/50'
                          : 'bg-slate-900/30 hover:bg-slate-700/30'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <div className={`w-4 h-4 rounded border-2 flex items-center justify-center transition-all ${
                          isActive ? 'border-indigo-500 bg-indigo-500' : 'border-slate-600'
                        }`}>
                          {isActive && (
                            <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                            </svg>
                          )}
                        </div>
                        <input
                          type="checkbox"
                          checked={isActive}
                          onChange={() => toggleProvince(province)}
                          className="sr-only"
                        />
                        <span className="text-sm text-white truncate">{province}</span>
                      </div>
                      <span className="text-xs text-slate-400 font-mono ml-2">{String(count)}</span>
                    </label>
                  );
                })}
            </div>
          ) : (
            <p className="text-xs text-slate-500 py-2">No province data available</p>
          )}
        </Section>

        {/* Status */}
        <Section
          title="Status"
          icon={Zap}
          isExpanded={expandedSections.status}
          onToggle={() => toggleSection('status')}
        >
          <div className="space-y-1.5">
            {(['operational', 'under_construction', 'decommissioned'] as const).map(status => {
              const isActive = filters.status.includes(status);
              const statusColors: Record<string, string> = {
                operational: 'bg-emerald-500',
                under_construction: 'bg-amber-500',
                decommissioned: 'bg-slate-500',
              };
              return (
                <label
                  key={status}
                  className={`flex items-center gap-2.5 p-2.5 rounded-lg cursor-pointer transition-all ${
                    isActive
                      ? 'bg-slate-700/70 ring-1 ring-slate-600/50'
                      : 'bg-slate-900/30 hover:bg-slate-700/30'
                  }`}
                >
                  <div className={`w-4 h-4 rounded border-2 flex items-center justify-center transition-all ${
                    isActive ? 'border-indigo-500 bg-indigo-500' : 'border-slate-600'
                  }`}>
                    {isActive && (
                      <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>
                  <input
                    type="checkbox"
                    checked={isActive}
                    onChange={() => toggleStatus(status)}
                    className="sr-only"
                  />
                  <div className={`w-2 h-2 rounded-full ${statusColors[status] || 'bg-slate-500'}`} />
                  <span className="text-sm text-white capitalize">{status.replace(/_/g, ' ')}</span>
                </label>
              );
            })}
          </div>
        </Section>
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-slate-700/50 bg-slate-900/30 rounded-b-xl">
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-400">Filtered Results</span>
          <span className="text-white font-bold">{stats?.totalInfrastructure || 0} items</span>
        </div>
      </div>
    </div>
  );
};
