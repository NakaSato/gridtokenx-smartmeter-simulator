import { NextResponse } from 'next/server';

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const limit = searchParams.get('limit') || '1000';
    const type = searchParams.get('type');
    const status = searchParams.get('status');

    // Hardcode to simulator backend; env var may be overridden
    const targetUrl = 'http://127.0.0.1:8082/api/v1/meters';
    const params = new URLSearchParams({ limit });
    if (type) params.set('type', type);
    if (status) params.set('status', status);

    const url = `${targetUrl}?${params.toString()}`;
    console.log('[API Proxy] Forwarding to:', url);

    try {
        const res = await fetch(url, {
            cache: 'no-store',
            headers: { 'Accept': 'application/json' },
        });
        if (!res.ok) {
            console.error('[API Proxy] Backend returned:', res.status, res.statusText);
            return NextResponse.json(
                { error: `Backend error: ${res.status}`, source: 'backend_error' },
                { status: res.status }
            );
        }
        const data = await res.json();
        return NextResponse.json(data);
    } catch (error: any) {
        console.error('[API Proxy] Fetch failed:', error.message, error.cause);
        return NextResponse.json(
            { error: 'Failed to fetch meters', message: error.message, source: 'proxy_error' },
            { status: 502 }
        );
    }
}
