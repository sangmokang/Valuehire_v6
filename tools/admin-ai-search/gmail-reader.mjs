// A read-only JSON-lines bridge. Reuses the host application's Gmail auth.
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { createInterface } from 'node:readline';
import { readTransport } from './read-transport.mjs';

const hostApp = process.env.AI_SEARCH_HOST_APP;
if (!hostApp) throw new Error('AI_SEARCH_HOST_APP is required');
process.loadEnvFile(path.join(hostApp, '.env.local'));
const moduleUrl = (file) => pathToFileURL(path.join(hostApp, 'tools/gmail-resume-clickup-match', file));
const { gmailDependencies } = await import(moduleUrl('backfill-ingestion.mjs'));
const { resolveGmailMemberAccounts } = await import(moduleUrl('lib/gmail-accounts.mjs'));
const deps = gmailDependencies(readTransport, 30000);
const account = resolveGmailMemberAccounts().find(a => a.email === process.env.AI_SEARCH_MAILBOX);
if (!account) throw new Error('Configured mailbox not found in existing Gmail account registry');
let token, tokenAt = 0, retries = 0;
async function accessToken() {
  if (!token || Date.now() - tokenAt > 3000000) {
    token = await deps.accessToken({ account });
    tokenAt = Date.now();
  }
  return token;
}
async function retry(read) {
  for (let attempt = 0; ; attempt++) {
    try { return await read(); }
    catch (error) {
      if (attempt >= 6 || ![401,403,408,429,500,502,503,504].includes(error.status)) throw error;
      if (error.status === 401) { token = undefined; }
      retries++;
      await new Promise(resolve => setTimeout(resolve, Math.min(60000, 1000 * 2 ** attempt) + Math.random() * 500));
    }
  }
}
// Only GET requests to the fixed Gmail API origin can be issued by this bridge.
async function readApi(resource, query = {}) {
  return retry(async () => {
    const url = new URL(`https://gmail.googleapis.com/gmail/v1/users/me/${resource}`);
    for (const [key, value] of Object.entries(query)) if (value !== null) url.searchParams.set(key, value);
    const response = await readTransport(url, { headers: { authorization: `Bearer ${await accessToken()}` }, signal: AbortSignal.timeout(30000) });
    if (!response.ok) {
      const error = new Error(`Gmail GET failed: HTTP ${response.status}: ${await response.text()}`);
      error.status = response.status;
      throw error;
    }
    return response.json();
  });
}
async function dispatch(operation, args) {
  switch (operation) {
    case 'labels': return readApi('labels');
    case 'profile': return readApi('profile');
    case 'stats': return { retries };
    case 'list': return readApi('messages', { labelIds: args.label_id, maxResults: '500', pageToken: args.page_token });
    case 'messages': {
      const output = [];
      for (let i = 0; i < args.ids.length; i += 25) {
        output.push(...await Promise.all(args.ids.slice(i, i + 25).map(async id => {
          try { return await readApi(`messages/${encodeURIComponent(id)}`, { format: 'full' }); }
          catch (error) {
            let metadata = { id };
            try { metadata = await readApi(`messages/${encodeURIComponent(id)}`, { format: 'metadata' }); }
            catch (metadataError) { metadata.metadata_error = metadataError.message; }
            return { ...metadata, collection_error: error.message, collection_status: 'FAILED' };
          }
        })));
      }
      return output;
    }
    case 'attachment': return readApi(`messages/${encodeURIComponent(args.message_id)}/attachments/${encodeURIComponent(args.attachment_id)}`);
    case 'attachment_text': {
      const supported = /\.(txt|csv|json|html?|pdf|docx?|rtf|odt)$/i.test(args.filename);
      if (!supported) return { status: 'unsupported', reason: 'unsupported_attachment_format' };
      const raw = await readApi(`messages/${encodeURIComponent(args.message_id)}/attachments/${encodeURIComponent(args.attachment_id)}`);
      const { attachmentBufferToText } = await import(moduleUrl('lib/textify.mjs'));
      return attachmentBufferToText({ buffer: Buffer.from(raw.data, 'base64url'), filename: args.filename, mimeType: args.mime_type });
    }
    default: throw new Error('Read operation not allowed');
  }
}
for await (const line of createInterface({ input: process.stdin })) {
  try {
    const input = JSON.parse(line);
    process.stdout.write(JSON.stringify({ ok: true, value: await dispatch(input.operation, input.args), retry_count: retries }) + '\n');
  } catch (error) {
    process.stdout.write(JSON.stringify({ ok: false, error: error.message, type: error.name, retry_count: retries }) + '\n');
  }
}
