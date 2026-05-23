import { NextResponse } from 'next/server';

const simulatorBase = process.env.SIMULATOR_URL || 'http://127.0.0.1:12010';
const API_BASE = `${simulatorBase}/api/v1/microgrid`;

async function proxyGET(path: string) {
    try {
        const res = await fetch(`${API_BASE}${path}`, {
            cache: 'no-store',
            headers: { 'Accept': 'application/json' },
        });
        return NextResponse.json(await res.json(), { status: res.status });
    } catch (e: unknown) {
        const message = e instanceof Error ? e.message : 'Unknown error';
        return NextResponse.json({ error: message }, { status: 502 });
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
    } catch (e: unknown) {
        const message = e instanceof Error ? e.message : 'Unknown error';
        return NextResponse.json({ error: message }, { status: 502 });
    }
}

export { proxyGET, proxyPOST };
