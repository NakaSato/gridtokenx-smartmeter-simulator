import { useState, useCallback } from 'react';

interface ViewState {
  longitude: number;
  latitude: number;
  zoom: number;
  pitch?: number;
  bearing?: number;
}

export function usePersistedViewState(key: string, defaults: ViewState) {
  const [viewState, setViewStateRaw] = useState<ViewState>(() => {
    try {
      const saved = localStorage.getItem(`map_view_${key}`);
      if (saved) return { ...defaults, ...JSON.parse(saved) };
    } catch {}
    return defaults;
  });

  const setViewState = useCallback((next: ViewState) => {
    setViewStateRaw(next);
    try {
      localStorage.setItem(`map_view_${key}`, JSON.stringify({
        longitude: next.longitude,
        latitude: next.latitude,
        zoom: next.zoom,
        pitch: next.pitch,
        bearing: next.bearing,
      }));
    } catch {}
  }, [key]);

  return [viewState, setViewState] as const;
}
