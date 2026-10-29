// Optional per-process DNS-over-HTTPS for runners without system DNS.
// TLS still validates the requested hostname; system DNS is never modified.
import https from 'node:https';

const cache = new Map();
async function address(hostname) {
  const cached = cache.get(hostname);
  if (cached && cached.until > Date.now()) return cached.ip;
  const response = await request(`https://1.1.1.1/dns-query?name=${encodeURIComponent(hostname)}&type=A`, {
    headers: { accept: 'application/dns-json' },
  });
  const body = await response.json();
  const answer = body.Answer?.find(item => item.type === 1);
  if (!answer) throw new Error('DNS-over-HTTPS returned no IPv4 address');
  cache.set(hostname, { ip: answer.data, until: Date.now() + answer.TTL * 1000 });
  return answer.data;
}
function request(url, options, ip) {
  return new Promise((resolve, reject) => {
    const req = https.request(url, {
      method: options.method === undefined ? 'GET' : options.method,
      headers: Object.fromEntries(new Headers(options.headers).entries()), signal: options.signal,
      ...(ip ? { lookup: (_host, _options, callback) => callback(null, [{ address: ip, family: 4 }]) } : {}),
    }, response => {
      const chunks = [];
      response.on('data', chunk => chunks.push(chunk));
      response.on('error', reject);
      response.on('end', () => resolve(new Response([204,205,304].includes(response.statusCode) ? null : Buffer.concat(chunks), {
        status: response.statusCode, headers: response.headers,
      })));
    });
    req.on('error', reject);
    if (options.body) req.write(String(options.body));
    req.end();
  });
}
export async function readTransport(url, options = {}) {
  if (process.env.AI_SEARCH_DOH !== '1') return fetch(url, options);
  const target = new URL(url);
  if (target.protocol !== 'https:') throw new Error('HTTPS required');
  return request(target, options, await address(target.hostname));
}
