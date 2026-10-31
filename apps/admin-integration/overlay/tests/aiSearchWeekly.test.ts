import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  guard: vi.fn(), user: vi.fn(), fetch: vi.fn(),
}));
vi.mock('@/src/auth/internalApiGuard', () => ({ requireInternalOpsAccess: mocks.guard }));
vi.mock('@/src/lib/supabase', () => ({ getRequestUser: mocks.user }));
import { GET } from '../app/api/admin/ai-search/[...path]/route';
import { safeEvidenceUrl } from '../src/admin/aiSearchWeeklyUrl';

describe('AI Search administrator boundary', () => {
  beforeEach(() => { vi.resetAllMocks(); mocks.guard.mockResolvedValue(null); vi.stubGlobal('fetch', mocks.fetch); vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL','https://db.example.invalid'); });
  it('requires a real session even when the existing development guard bypasses auth', async () => {
    mocks.user.mockResolvedValue(null);
    const response = await GET(new Request('http://localhost/api/admin/ai-search/candidates/secret'), { params: Promise.resolve({ path: ['candidates','secret'] }) });
    expect(response.status).toBe(401); expect(mocks.fetch).not.toHaveBeenCalled();
  });
  it('forbids authenticated external customers from reading candidate raw data', async () => {
    mocks.user.mockResolvedValue({ email: 'customer@example.invalid' });
    const response = await GET(new Request('http://localhost/api/admin/ai-search/candidates/secret'), { params: Promise.resolve({ path: ['candidates','secret'] }) });
    expect(response.status).toBe(403); expect(mocks.fetch).not.toHaveBeenCalled();
  });
  it('passes bound filter and pagination arguments to the module RPC after auth', async () => {
    mocks.user.mockResolvedValue({ email: 'operator@valueconnect.kr' });
    mocks.fetch.mockResolvedValue(Response.json({ rows: [], total: 0 }));
    const response = await GET(new Request('http://localhost/api/admin/ai-search/weekly/2026-W44?q=O%27Reilly&limit=1000&offset=50'), { params: Promise.resolve({ path: ['weekly','2026-W44'] }) });
    expect(response.status).toBe(200);
    expect(response.headers.get('cache-control')).toBe('private, no-store');
    const [url, options] = mocks.fetch.mock.calls[0]!;
    expect(url).toBe('https://db.example.invalid/rest/v1/rpc/admin_ai_search_read');
    expect(options.method).toBe('POST');
    expect(JSON.parse(options.body)).toEqual({ p_action: 'weekly', p_args: { week: '2026-W44', q: "O'Reilly", limit: 200, offset: 50 } });
  });
  it('passes executor and shared weekly Batch number filters to the RPC', async () => {
    mocks.user.mockResolvedValue({ email: 'operator@valueconnect.kr' });
    mocks.fetch.mockResolvedValue(Response.json({ rows: [], total: 0 }));
    await GET(new Request('http://localhost/api/admin/ai-search/weekly/2026-W45?actor=CODEX&batch=W45-03'), { params: Promise.resolve({ path: ['weekly','2026-W45'] }) });
    expect(JSON.parse(mocks.fetch.mock.calls[0]![1].body).p_args).toEqual({ week: '2026-W45', actor: 'CODEX', batch: 'W45-03', limit: 50, offset: 0 });
  });
  it('returns an explicit failure when the database read fails', async () => {
    mocks.user.mockResolvedValue({ email: 'operator@valueconnect.kr' });
    mocks.fetch.mockResolvedValue(Response.json({ message: 'private database details' }, { status: 500 }));
    const response = await GET(new Request('http://localhost/api/admin/ai-search/weeks'), { params: Promise.resolve({ path: ['weeks'] }) });
    expect(response.status).toBe(503);
    expect(await response.text()).not.toContain('private database details');
  });
  it.each(['javascript:alert(1)','data:text/html,hello','file:///etc/passwd'])('rejects unsafe evidence URLs: %s', url => {
    expect(safeEvidenceUrl(url)).toBeNull();
  });
  it('rejects URLs containing user information', () => {
    const url = new URL('https://example.invalid/');
    url.username = 'u'; url.password = 'p';
    expect(safeEvidenceUrl(url.href)).toBeNull();
  });
  it('retains identity parameters in original profile links', () => {
    expect(safeEvidenceUrl('https://example.invalid/profile?res_idx=123')).toBe('https://example.invalid/profile?res_idx=123');
  });
});
