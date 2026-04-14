import { NextResponse } from 'next/server';

const API_BASE = 'http://127.0.0.1:8082/api/v1/microgrid';

async function proxyGET(path: string) {
    try {
        const res = await fetch(`${API_BASE}${path}`, {
            cache: 'no-store',
            headers: { 'Accept': 'application/json' },
        });
        return NextResponse.json(await res.json(), { status: res.status });
    } catch (e: any) {
        return NextResponse.json({ error: e.message }, { status: 502 });
    }
}

async function proxyPOST(path: string, body: string) {
    try {
        const res = await fetch(`${API_BASE}${path}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
            body,
        });
        return NextResponse.json(await res.json(), { status: res.status });
    } catch (e: any) {
        return NextResponse.json({ error: e.message }, { status: 502 });
    }
}

export { proxyGET, proxyPOST };
