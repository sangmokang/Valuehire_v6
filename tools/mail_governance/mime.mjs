// Pure MIME construction only: no credentials, filesystem, network, or journal.
import { createHash } from 'node:crypto';
export const MIRROR_RECIPIENT = 'dev@valueconnect.kr';
export const MIRROR_MARKER = '[VC-MIRROR:v1]';
export const MAX_TRANSPORT_BYTES = 20 * 1024 * 1024;
const ZIP_NAME = Buffer.from('original.eml');
const CRC_TABLE = Array.from({ length: 256 }, (_, n) => {
  for (let bit = 0; bit < 8; bit++) n = n & 1 ? 0xedb88320 ^ (n >>> 1) : n >>> 1;
  return n >>> 0;
});

function crc32(bytes) {
  let crc = 0xffffffff;
  for (const byte of bytes) crc = CRC_TABLE[(crc ^ byte) & 255] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}

export function buildOriginalZip(originalBytes) {
  if (!(originalBytes instanceof Uint8Array) || originalBytes.length === 0) throw new Error('Original RFC bytes must not be empty');
  if (originalBytes.length > MAX_TRANSPORT_BYTES) throw new Error('20 MiB transport limit exceeded');
  const crc = crc32(originalBytes);
  const local = Buffer.alloc(30);
  local.writeUInt32LE(0x04034b50, 0); local.writeUInt16LE(20, 4); local.writeUInt16LE(0x800, 6);
  local.writeUInt16LE(0x21, 12); local.writeUInt32LE(crc, 14);
  local.writeUInt32LE(originalBytes.length, 18); local.writeUInt32LE(originalBytes.length, 22); local.writeUInt16LE(ZIP_NAME.length, 26);
  const central = Buffer.alloc(46);
  central.writeUInt32LE(0x02014b50, 0); central.writeUInt16LE(20, 4); central.writeUInt16LE(20, 6); central.writeUInt16LE(0x800, 8);
  central.writeUInt16LE(0x21, 14); central.writeUInt32LE(crc, 16);
  central.writeUInt32LE(originalBytes.length, 20); central.writeUInt32LE(originalBytes.length, 24); central.writeUInt16LE(ZIP_NAME.length, 28);
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0); end.writeUInt16LE(1, 8); end.writeUInt16LE(1, 10);
  end.writeUInt32LE(central.length + ZIP_NAME.length, 12); end.writeUInt32LE(local.length + ZIP_NAME.length + originalBytes.length, 16);
  const zip = Buffer.concat([local, ZIP_NAME, originalBytes, central, ZIP_NAME, end]);
  if (zip.length > MAX_TRANSPORT_BYTES) throw new Error('20 MiB transport limit exceeded');
  return zip;
}

export function extractOriginalEml(zipBytes) {
  const bytes = Buffer.from(zipBytes);
  const bad = () => { throw new Error('Invalid original ZIP archive'); };
  if (bytes.length < 22 || bytes.length > MAX_TRANSPORT_BYTES) return bad();
  const end = bytes.length - 22;
  if (bytes.readUInt32LE(end) !== 0x06054b50 || bytes.readUInt16LE(end + 4) || bytes.readUInt16LE(end + 6) || bytes.readUInt16LE(end + 8) !== 1 || bytes.readUInt16LE(end + 10) !== 1 || bytes.readUInt16LE(end + 20)) return bad();
  const central = bytes.readUInt32LE(end + 16), centralSize = bytes.readUInt32LE(end + 12);
  if (central + centralSize !== end || centralSize !== 46 + ZIP_NAME.length || central < 30 + ZIP_NAME.length || bytes.readUInt32LE(central) !== 0x02014b50) return bad();
  if (bytes.readUInt16LE(central + 8) !== 0x800 || bytes.readUInt16LE(central + 10) !== 0 || bytes.readUInt16LE(central + 28) !== ZIP_NAME.length || bytes.readUInt16LE(central + 30) || bytes.readUInt16LE(central + 32) || bytes.readUInt16LE(central + 34) || bytes.readUInt32LE(central + 42)) return bad();
  if (!bytes.subarray(central + 46, central + 46 + ZIP_NAME.length).equals(ZIP_NAME)) return bad();
  if (bytes.readUInt32LE(0) !== 0x04034b50 || bytes.readUInt16LE(6) !== 0x800 || bytes.readUInt16LE(8) !== 0 || bytes.readUInt16LE(26) !== ZIP_NAME.length || bytes.readUInt16LE(28) !== 0 || !bytes.subarray(30, 30 + ZIP_NAME.length).equals(ZIP_NAME)) return bad();
  const size = bytes.readUInt32LE(central + 24), crc = bytes.readUInt32LE(central + 16);
  if (size === 0 || bytes.readUInt32LE(central + 20) !== size || bytes.readUInt32LE(18) !== size || bytes.readUInt32LE(22) !== size || bytes.readUInt32LE(14) !== crc || 30 + ZIP_NAME.length + size !== central) return bad();
  const original = bytes.subarray(30 + ZIP_NAME.length, central);
  if (crc32(original) !== crc) return bad();
  return Buffer.from(original);
}

function normalizedMessageId(value) {
  if (typeof value !== 'string' || value.length === 0 || /[\s\u0000-\u0020\u007f-\uffff]/u.test(value)) throw new Error('Invalid RFC Message-ID');
  const id = value.startsWith('<') && value.endsWith('>') ? value.slice(1, -1) : value;
  const atom = "[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+";
  const dotAtom = `${atom}(?:\\.${atom})*`;
  const literal = '\\[[\\x21-\\x5a\\x5e-\\x7e]+\\]';
  if (!new RegExp(`^${dotAtom}@(?:${dotAtom}|${literal})$`).test(id)) throw new Error('Invalid RFC Message-ID');
  return `<${id}>`;
}

export function verifyReceivedOriginal(originalBytes, expectedSha256, expectedRfcMessageId) {
  if (!(originalBytes instanceof Uint8Array) || originalBytes.length === 0) throw new Error('Original RFC bytes must not be empty');
  if (originalBytes.length > MAX_TRANSPORT_BYTES) throw new Error('20 MiB transport limit exceeded');
  if (typeof expectedSha256 !== 'string' || expectedSha256.length !== 64 || !/^[a-f0-9]{64}$/.test(expectedSha256)) throw new Error('Invalid expected RFC SHA-256');
  const expectedId = normalizedMessageId(expectedRfcMessageId);
  // Snapshot the exact received bytes once so hashing and parsing share authority.
  const bytes = Buffer.from(originalBytes);
  const actualSha256 = createHash('sha256').update(bytes).digest('hex');
  if (actualSha256 !== expectedSha256) throw new Error('Received original RFC bytes SHA-256 mismatch');
  const crlfBoundary = bytes.indexOf('\r\n\r\n');
  const lfBoundary = bytes.indexOf('\n\n');
  const boundaries = [crlfBoundary, lfBoundary].filter(index => index >= 0);
  if (boundaries.length === 0) throw new Error('Original RFC header/body boundary missing');
  const headers = bytes.subarray(0, Math.min(...boundaries)).toString('latin1');
  if (/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/u.test(headers)) throw new Error('Invalid original RFC headers');
  const messageIds = [];
  let current = null;
  const finish = () => {
    if (current?.name.toLowerCase() === 'message-id') messageIds.push(current.value.replace(/^[ \t]+|[ \t]+$/g, ''));
  };
  for (const line of headers.split(/\r\n|\n|\r/)) {
    if (/^[ \t]/.test(line)) {
      if (!current) throw new Error('Invalid original RFC header folding');
      current.value += ` ${line.replace(/^[ \t]+/, '')}`;
      continue;
    }
    finish();
    const matched = /^([\x21-\x39\x3b-\x7e]+):(.*)$/.exec(line);
    if (!matched) throw new Error('Invalid original RFC header field');
    current = { name: matched[1], value: matched[2] };
  }
  finish();
  if (messageIds.length !== 1) throw new Error('Exactly one original RFC Message-ID required');
  const actualId = normalizedMessageId(messageIds[0]);
  if (actualId !== expectedId) throw new Error('Received original RFC Message-ID mismatch');
  return { original_sha256: actualSha256, rfc_message_id: actualId };
}

export function assertHeaderValue(value) {
  if (typeof value !== 'string' || /[\r\n\u0000]/.test(value)) throw new Error('Invalid MIME header value');
  return value;
}

function escapeHtml(value) {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function base64Lines(bytes) {
  const encoded = Buffer.from(bytes).toString('base64');
  const lines = [];
  for (let offset = 0; offset < encoded.length; offset += 76) lines.push(encoded.slice(offset, offset + 76));
  return lines.join('\r\n');
}

function encodedSubject(text) {
  // RFC 2047 encoded words stay below 75 characters, without splitting UTF-8.
  const words = [];
  let chunk = '';
  for (const char of text) {
    if (Buffer.byteLength(chunk + char) > 42) {
      words.push(`=?UTF-8?B?${Buffer.from(chunk).toString('base64')}?=`);
      chunk = '';
    }
    chunk += char;
  }
  if (chunk) words.push(`=?UTF-8?B?${Buffer.from(chunk).toString('base64')}?=`);
  return words.join('\r\n ');
}

export function buildMirrorMime(options) {
  if ('to' in options || 'receiver' in options || 'recipient' in options) throw new Error('Mirror recipient is fixed');
  const { sender, opId, sourceId, rfcId, subject, labels, note = '', originalHtml = '', originalText = '', originalBytes, now = new Date() } = options;
  if ([note, originalHtml, originalText].some(value => typeof value !== 'string')) throw new Error('Invalid mirror body text');
  assertHeaderValue(sender);
  if (!/^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(sender)) throw new Error('Invalid sender address');
  if (!/^[a-f0-9]{64}$/.test(opId)) throw new Error('Invalid operation ID');
  if (!/^[a-f0-9]{8,64}$/.test(sourceId)) throw new Error('Invalid source message ID');
  if (!assertHeaderValue(rfcId).trim()) throw new Error('Original RFC Message-ID is required');
  if (!Array.isArray(labels) || labels.some(label => typeof label !== 'string' || /[\r\n\u0000]/.test(label))) throw new Error('Invalid canonical labels');
  if (!(originalBytes instanceof Uint8Array) || originalBytes.length === 0) throw new Error('Original RFC bytes must not be empty');
  if (originalBytes.length > MAX_TRANSPORT_BYTES) throw new Error('20 MiB transport limit exceeded');
  if (!(now instanceof Date) || Number.isNaN(now.getTime())) throw new Error('Invalid message date');
  const archiveBytes = buildOriginalZip(originalBytes);
  const originalSha256 = createHash('sha256').update(originalBytes).digest('hex');

  const subjectText = `${MIRROR_MARKER} ${assertHeaderValue(subject)}`;
  const mixed = `vc-mirror-${opId}-mixed`;
  const alternative = `vc-mirror-${opId}-alternative`;
  const metadata = [MIRROR_MARKER, `Operation: ${opId}`, `Original-Message-ID: ${rfcId}`, `Original-EML-SHA256: ${originalSha256}`, `Canonical-Labels: ${labels.join(', ')}`, `Source-Gmail-ID: ${sourceId}`, `Note: ${note}`];
  const prefix = `<div style="padding:16px;border:1px solid #ddd;font-family:Arial,sans-serif;line-height:1.55">${metadata.map(value => `<div>${escapeHtml(value)}</div>`).join('')}<div>원문 RFC 전체는 original.zip 안의 original.eml로 보존했습니다.</div></div><hr>`;
  const textBody = `${metadata.join('\n')}\n원문 RFC 전체는 original.zip 안의 original.eml로 보존했습니다.\n\n${originalText}`;
  const renderedOriginal = originalHtml.length > 0 ? originalHtml : `<pre>${escapeHtml(originalText)}</pre>`;
  const htmlBody = prefix + renderedOriginal;
  if (Buffer.byteLength(textBody) + Buffer.byteLength(htmlBody) > MAX_TRANSPORT_BYTES) throw new Error('20 MiB transport limit exceeded');
  const chunks = [
    `From: ${sender}`, `To: ${MIRROR_RECIPIENT}`, `Subject: ${encodedSubject(subjectText)}`,
    `Date: ${now.toUTCString()}`, `Message-ID: <vc-mirror-${opId}@valueconnect.kr>`,
    `X-VC-Mirror-Operation: ${opId}`, `X-VC-Source-RFC-Message-ID: ${rfcId}`, `X-VC-Original-SHA256: ${originalSha256}`,
    'MIME-Version: 1.0', `Content-Type: multipart/mixed; boundary="${mixed}"`, '',
    `--${mixed}`, `Content-Type: multipart/alternative; boundary="${alternative}"`, '',
    `--${alternative}`, 'Content-Type: text/plain; charset=UTF-8', 'Content-Transfer-Encoding: base64', '', base64Lines(Buffer.from(textBody)),
    `--${alternative}`, 'Content-Type: text/html; charset=UTF-8', 'Content-Transfer-Encoding: base64', '', base64Lines(Buffer.from(htmlBody)),
    `--${alternative}--`, '', `--${mixed}`,
    'Content-Type: application/zip; name="original.zip"',
    'Content-Disposition: attachment; filename="original.zip"', 'Content-Transfer-Encoding: base64', '',
    base64Lines(archiveBytes), `--${mixed}--`, '',
  ];
  const mime = Buffer.from(chunks.join('\r\n'));
  const payload = JSON.stringify({ raw: mime.toString('base64url') });
  if (mime.length > MAX_TRANSPORT_BYTES || Buffer.byteLength(payload) > MAX_TRANSPORT_BYTES) throw new Error('20 MiB transport limit exceeded');
  return { mime, payload, subjectText, archiveBytes, originalSha256 };
}
