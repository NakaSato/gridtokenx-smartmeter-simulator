import type {
    GridTelemetryResponse,
    GridTopologyResponse,
    MeterListResponse,
    MeterReading,
    MeterSummary,
    RunSeriesResponse,
    SimulationStatusResponse,
} from './types';

export type ApiCall = <T>(
    path: string,
    options?: RequestInit,
    successMessage?: string,
    errorMessage?: string
) => Promise<T | null>;

const API_PREFIX = '/api/v1';

const endpoint = (path: string) => `${API_PREFIX}${path}`;

const json = (body: unknown): RequestInit => ({
    body: JSON.stringify(body),
});

export function createSimulatorApi(apiCall: ApiCall) {
    return {
        getStatus: () => apiCall<SimulationStatusResponse>(endpoint('/simulation/status')),
        action: (action: 'start' | 'stop' | 'pause' | 'resume' | 'step') =>
            apiCall<{ status: string; last_tick?: Record<string, unknown> }>(endpoint(`/simulation/actions/${action}`), { method: 'POST' }),
        startDeterministic: (payload: { seed?: number; start_time?: string; interval?: number; num_meters?: number; autostart?: boolean }) =>
            apiCall<{ status: string; seed: number; start_time: string; interval: number; total_meters: number; running: boolean }>(
                endpoint('/simulation/actions/start-deterministic'),
                { method: 'POST', ...json(payload) }
            ),
        updateEnvironment: (updates: { weather?: string; grid_stress?: number; topology?: string }) =>
            apiCall<{ status: string; new_count?: number; [key: string]: unknown }>(endpoint('/simulation/environment'), {
                method: 'PATCH',
                ...json(updates),
            }),
        updateMeterCount: (payload: { count: number; [key: string]: unknown }) =>
            apiCall<{ status: string; new_count: number }>(endpoint('/meters/count'), {
                method: 'PUT',
                ...json(payload),
            }),
        listMeters: (params: { limit?: number; type?: string } = {}) => {
            const search = new URLSearchParams();
            if (params.limit) search.set('limit', String(params.limit));
            if (params.type) search.set('type', params.type);
            const query = search.toString();
            return apiCall<MeterListResponse>(endpoint(`/meters${query ? `?${query}` : ''}`));
        },
        getMeter: (meterId: string) => apiCall<MeterSummary>(endpoint(`/meters/${encodeURIComponent(meterId)}`)),
        createMeter: (payload: Record<string, unknown>) =>
            apiCall<{ status: string; meter: MeterSummary }>(endpoint('/meters'), {
                method: 'POST',
                ...json(payload),
            }),
        patchMeter: (meterId: string, payload: Record<string, unknown>) =>
            apiCall<{ status: string; meter_id: string; patched_fields: string[] }>(endpoint(`/meters/${encodeURIComponent(meterId)}`), {
                method: 'PATCH',
                ...json(payload),
            }),
        deleteMeter: (meterId: string) =>
            apiCall<{ status: string; meter_id: string }>(endpoint(`/meters/${encodeURIComponent(meterId)}`), { method: 'DELETE' }),
        getMeterReadings: (meterId: string, limit = 100) =>
            apiCall<{ meter_id: string; readings: MeterReading[]; total: number }>(
                endpoint(`/meters/${encodeURIComponent(meterId)}/readings?limit=${limit}`)
            ),
        overrideReading: (meterId: string, payload: { value: number; field: 'generation' | 'consumption' | string }) =>
            apiCall<{ status: string; meter_id: string; field: string; value: number }>(
                endpoint(`/meters/${encodeURIComponent(meterId)}/readings/override`),
                {
                    method: 'POST',
                    ...json(payload),
                }
            ),
        getCurrentRun: () => apiCall<{ run_id: string | null }>(endpoint('/history/run/current')),
        listRuns: () => apiCall<{ count: number; runs: string[] }>(endpoint('/history/runs')),
        getRunSeries: (params: { run_id?: string; meter_id?: string } = {}) => {
            const search = new URLSearchParams();
            if (params.run_id) search.set('run_id', params.run_id);
            if (params.meter_id) search.set('meter_id', params.meter_id);
            const query = search.toString();
            return apiCall<RunSeriesResponse>(endpoint(`/history/run/series${query ? `?${query}` : ''}`));
        },
        getGridStatus: () => apiCall<Record<string, unknown>>(endpoint('/grid/status')),
        getGridTopology: () => apiCall<GridTopologyResponse>(endpoint('/grid/topology')),
        getGridTelemetry: () => apiCall<GridTelemetryResponse>(endpoint('/grid/telemetry')),
        getGridStats: () => apiCall<Record<string, unknown>>(endpoint('/grid/stats')),
    };
}
