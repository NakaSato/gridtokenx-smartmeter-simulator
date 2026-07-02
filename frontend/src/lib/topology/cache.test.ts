import { test, mock } from 'node:test';
import assert from 'node:assert/strict';
import {
    getTopologyCache,
    setTopologyCache,
    clearTopologyCache,
    TOPOLOGY_CACHE_TTL_MS,
} from './cache.ts';
import type { TopologyGraphData } from './types.ts';

const data = (label: string): TopologyGraphData => ({
    nodes: [{ id: 'bus-0', label, kind: 'service' }] as TopologyGraphData['nodes'],
    links: [],
});
const counts = { buses: 1, lines: 0, meters: 1 };

test('miss on empty cache', () => {
    clearTopologyCache();
    assert.equal(getTopologyCache('http://a'), null);
});

test('hit returns stored data and counts for the same key', () => {
    clearTopologyCache();
    setTopologyCache('http://a', data('a'), counts);
    const hit = getTopologyCache('http://a');
    assert.ok(hit);
    assert.equal(hit.data.nodes[0].label, 'a');
    assert.deepEqual(hit.counts, counts);
});

test('keys are independent per API target', () => {
    clearTopologyCache();
    setTopologyCache('http://a', data('a'), counts);
    assert.equal(getTopologyCache('http://b'), null);
});

test('entry expires after TTL and is evicted', () => {
    clearTopologyCache();
    mock.timers.enable({ apis: ['Date'], now: 1_000_000 });
    try {
        setTopologyCache('http://a', data('a'), counts);
        mock.timers.setTime(1_000_000 + TOPOLOGY_CACHE_TTL_MS); // exactly at TTL: still fresh
        assert.ok(getTopologyCache('http://a'));
        mock.timers.setTime(1_000_000 + TOPOLOGY_CACHE_TTL_MS + 1); // past TTL: stale
        assert.equal(getTopologyCache('http://a'), null);
    } finally {
        mock.timers.reset();
    }
});

test('clearTopologyCache drops all keys', () => {
    clearTopologyCache();
    setTopologyCache('http://a', data('a'), counts);
    setTopologyCache('http://b', data('b'), counts);
    clearTopologyCache();
    assert.equal(getTopologyCache('http://a'), null);
    assert.equal(getTopologyCache('http://b'), null);
});
