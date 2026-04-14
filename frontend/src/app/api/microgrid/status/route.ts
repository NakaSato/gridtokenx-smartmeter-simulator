import { proxyGET } from '../proxy-utils';
export async function GET() { return proxyGET('/status'); }
