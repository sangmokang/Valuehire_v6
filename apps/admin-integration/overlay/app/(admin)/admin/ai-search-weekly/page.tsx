import { redirect, notFound } from 'next/navigation';
import { getServerPageUser } from '@/src/lib/supabase';
import { isAllowedCompanyDomain } from '@/src/auth/recruiterSignupPolicy';
import AiSearchWeekly from './weekly-client';

export const dynamic = 'force-dynamic';
export default async function AiSearchWeeklyPage() {
  const user = await getServerPageUser();
  if (!user) redirect('/login?next=/admin/ai-search-weekly');
  if (!isAllowedCompanyDomain(user.email)) notFound();
  return <AiSearchWeekly />;
}
