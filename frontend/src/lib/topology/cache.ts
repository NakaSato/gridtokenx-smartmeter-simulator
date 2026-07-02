import type { TopologyGraphData } from './types';

/**
 * Module-level stale-while-revalidate cache for the *static* grid topology.
 *
 * The `/grid/topology` + `/meters` payloads are large and the structure
 * (buses, lines, meter assignment) is effectively immutable for the lifetime
 * of a simulation run — only telemetry changes tick to tick. Re-downloading
 * and re-building the whole graph on every navigation to the topology page is
 * wasted bandwidth + a blank-screen stall.
 *
 * Strategy: keep the built graph keyed by API target. A cache hit renders
 * instantly and skips the heavy refetch. A short TTL bounds staleness so the
 * graph self-heals even if an explicit invalidation point is missed, and
 * structural mutations (fleet rebuild, meter add/delete) call
 * `clearTopologyCache()` for immediate correctness.
 */

export interface TopologyCounts {
    buses: number;
    lines: number;
    meters: number;
}

interface CacheEntry {
    data: TopologyGraphData;
    counts: TopologyCounts;
    ts: number;
}

/** How long a cached topology is served without revalidation (ms). */
export const TOPOLOGY_CACHE_TTL_MS = 60_000;

const store = new Map<string, CacheEntry>();

/** Return the cached topology for `key` if present and fresher than the TTL. */
export function getTopologyCache(key: string): { data: TopologyGraphData; counts: TopologyCounts } | null {
    const entry = store.get(key);
    if (!entry) return null;
    if (Date.now() - entry.ts > TOPOLOGY_CACHE_TTL_MS) {
        store.delete(key);
        return null;
    }
    return { data: entry.data, counts: entry.counts };
}

/** Store the freshly-built topology graph for `key`. */
export function setTopologyCache(key: string, data: TopologyGraphData, counts: TopologyCounts): void {
    store.set(key, { data, counts, ts: Date.now() });
}

/**
 * Drop cached topology. Call after any mutation that changes grid structure
 * (fleet rebuild, meter add/delete) so the next visit refetches.
 */
export function clearTopologyCache(): void {
    store.clear();
}
