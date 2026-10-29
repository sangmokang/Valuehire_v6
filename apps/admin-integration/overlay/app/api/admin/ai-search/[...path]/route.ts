import { requireAiSearchAccess } from '@/src/admin/aiSearchWeeklyAccess';

export const dynamic = 'force-dynamic';
export async function GET(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const denied = await requireAiSearchAccess(request);
  if (denied) return denied;
  const { path } = await context.params;
  const action = path[0];
  if (!action || !['weeks','weekly','candidates','batches','high-score-uncontacted','review-queue','collection-status'].includes(action)) {
    return Response.json({ error: 'not_found' }, { status: 404 });
  }
  const query = new URL(request.url).searchParams;
  const args: Record<string, string | number> = {};
  for (const field of ['q','actor','company','position','channel','contact_status','sort']) {
    const value = query.get(field);
    if (value !== null) args[field] = value.slice(0, 200);
  }
  if (action === 'weekly' || action === 'high-score-uncontacted') {
    const week = path[1] === undefined ? query.get('week') : path[1];
    if (!week || !/^\d{4}-W(?:0[1-9]|[1-4]\d|5[0-3])$/.test(week)) {
      return Response.json({ error: 'invalid_week' }, { status: 400 });
    }
    args.week = week;
  }
  if (action === 'candidates' || action === 'batches') {
    if (!path[1] || !/^[A-Za-z0-9_-]{1,100}$/.test(path[1])) {
      return Response.json({ error: 'invalid_id' }, { status: 400 });
    }
    args.id = path[1];
  }
  for (const [field, fallback] of [['limit',50],['offset',0]] as const) {
    const text = query.get(field);
    const value = text === null ? fallback : Number(text);
    if (!Number.isSafeInteger(value) || value < (field === 'limit' ? 1 : 0)) {
      return Response.json({ error: 'invalid_pagination' }, { status: 400 });
    }
    args[field] = field === 'limit' ? Math.min(200,value) : value;
  }
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_SUPABASE_URL}/rest/v1/rpc/admin_ai_search_read`, {
      method: 'POST', cache: 'no-store', signal: AbortSignal.timeout(30000),
      headers: { apikey: process.env.SUPABASE_SERVICE_ROLE_KEY!,
        authorization: `Bearer ${process.env.SUPABASE_SERVICE_ROLE_KEY}`, 'content-type': 'application/json' },
      body: JSON.stringify({ p_action: action, p_args: args }),
    });
    if (!response.ok) return Response.json({ status: 'FAILED', reason: 'ai_search_database_read_failed' }, { status: 503 });
    const data: unknown = await response.json();
    if (data === null) return Response.json({ error: 'not_found' }, { status: 404 });
    return Response.json(data, { headers: { 'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff' } });
  } catch {
    return Response.json({ status: 'FAILED', reason: 'ai_search_service_unavailable' }, { status: 503 });
  }
}
