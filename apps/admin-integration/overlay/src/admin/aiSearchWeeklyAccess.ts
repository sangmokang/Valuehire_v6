import { requireInternalOpsAccess } from '@/src/auth/internalApiGuard';
import { getRequestUser } from '@/src/lib/supabase';
import { isAllowedCompanyDomain } from '@/src/auth/recruiterSignupPolicy';

/** Reuse the internal guard, then enforce sessions even on local/preview hosts. */
export async function requireAiSearchAccess(request: Request): Promise<Response | null> {
  const denied = await requireInternalOpsAccess(request);
  if (denied) return denied;
  const user = await getRequestUser(request);
  if (!user) return Response.json({ error: 'unauthenticated' }, { status: 401 });
  if (!isAllowedCompanyDomain(user.email)) {
    return Response.json({ error: 'forbidden' }, { status: 403 });
  }
  return null;
}

