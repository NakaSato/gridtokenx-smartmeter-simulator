import { NextResponse } from 'next/server';

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const limit = searchParams.get('limit') || '1000';
    const status = searchParams.get('status') || 'operating';
    const renewable_only = searchParams.get('renewable_only');

    const targetUrl = `http://127.0.0.1:8082/api/v1/power-plants/`;
    const params = new URLSearchParams({ limit, status });
    if (renewable_only === 'true') params.set('renewable_only', 'true');

    const url = `${targetUrl}?${params.toString()}`;

    try {
        const res = await fetch(url, { cache: 'no-store', headers: { 'Accept': 'application/json' } });
        if (!res.ok) return NextResponse.json({ error: `Backend ${res.status}` }, { status: res.status });
        return NextResponse.json(await res.json());
    } catch (error: any) {
        console.error('[API Proxy /power-plants]', error.message);
        return NextResponse.json({ error: error.message }, { status: 502 });
    }
}
