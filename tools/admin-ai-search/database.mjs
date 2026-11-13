import { readFile } from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';
import { readTransport } from './read-transport.mjs';

const prefix = 'admin_ai_search_';
export async function databaseQuery(query) {
  const hostApp = process.env.AI_SEARCH_HOST_APP;
  if (!hostApp) throw new Error('AI_SEARCH_HOST_APP required');
  const project = (await readFile(path.join(hostApp, 'supabase/.temp/project-ref'), 'utf8')).trim();
  const token = (await readFile(path.join(os.homedir(), '.supabase/access-token'), 'utf8')).trim();
  const response = await readTransport(`https://api.supabase.com/v1/projects/${project}/database/query`, {
    method: 'POST', headers: { authorization: `Bearer ${token}`, 'content-type': 'application/json' },
    body: JSON.stringify({ query }), signal: AbortSignal.timeout(120000),
  });
  if (!response.ok) throw new Error(`Database query HTTP ${response.status}: ${await response.text()}`);
  return response.json();
}

export async function upsert(table, documents) {
  if (!table.startsWith(prefix) || !/^[a-z_]+$/.test(table)) throw new Error('Module table required');
  const hostApp = process.env.AI_SEARCH_HOST_APP;
  if (!hostApp) throw new Error('AI_SEARCH_HOST_APP required');
  process.loadEnvFile(path.join(hostApp, '.env.local'));
  const response = await readTransport(`${process.env.NEXT_PUBLIC_SUPABASE_URL}/rest/v1/${table}?on_conflict=id`, {
    method: 'POST', headers: {
      apikey: process.env.SUPABASE_SERVICE_ROLE_KEY,
      authorization: `Bearer ${process.env.SUPABASE_SERVICE_ROLE_KEY}`,
      'content-type': 'application/json', prefer: 'resolution=merge-duplicates,return=minimal',
    }, body: JSON.stringify(documents), signal: AbortSignal.timeout(60000),
  });
  if (!response.ok) throw new Error(`Module upsert ${table}: HTTP ${response.status}`);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const mode = process.argv[2];
  if (!['--check','--apply'].includes(mode)) throw new Error('Use --check or --apply');
  const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
  const migration = await readFile(path.join(root, 'supabase/migrations/20261029090000_admin_ai_search_weekly.sql'), 'utf8');
  const checks = await readFile(path.join(root, 'tools/admin-ai-search/migration-check.sql'), 'utf8');
  const result = await databaseQuery(`BEGIN;\n${migration}\n${checks}\n${mode === '--apply' ? 'COMMIT' : 'ROLLBACK'};`);
  console.log(JSON.stringify({ status: 'PASS', mode, result }));
}
