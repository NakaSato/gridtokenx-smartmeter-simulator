import { proxyPOST } from '../../proxy-utils';
export async function POST(request: Request) {
    const body = await request.text();
    return proxyPOST('/pcc/mode', body);
}
