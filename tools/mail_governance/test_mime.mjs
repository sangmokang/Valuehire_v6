import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { buildMirrorMime, buildOriginalZip, extractOriginalEml, MAX_TRANSPORT_BYTES, MIRROR_MARKER, MIRROR_RECIPIENT } from './mime.mjs';

function sample(overrides = {}) {
  return {
    sender: 'sender@example.test', opId: 'a'.repeat(64), sourceId: '1234567890abcdef',
    rfcId: '<original@example.test>', subject: '합성 제목', labels: ['01JD'],
    note: 'Synthetic note', originalHtml: '<div>Synthetic original</div>', originalText: 'Synthetic original',
    originalBytes: Buffer.from('Message-ID: <original@example.test>\r\n\r\nSynthetic original\n'),
    now: new Date(0), ...overrides,
  };
}

function attachmentBase64(mime) {
  const attachment = mime.toString().split('Content-Type: application/zip; name="original.zip"\r\n')[1];
  assert.ok(attachment);
  return attachment.split('\r\n\r\n')[1].split('\r\n--vc-mirror-')[0];
}

test('recipient is fixed and explicit override is refused', () => {
  const made = buildMirrorMime(sample());
  assert.ok(made.mime.toString().includes(`\r\nTo: ${MIRROR_RECIPIENT}\r\n`));
  for (const key of ['to', 'receiver', 'recipient']) assert.throws(() => buildMirrorMime(sample({ [key]: 'other@example.test' })), /fixed/);
});

test('RFC attachment preserves every byte, including binary and mixed newlines', () => {
  const originalBytes = Buffer.from([0, 1, 13, 10, 255, 254, 128, ...Buffer.from('한글\nraw\r\nbytes')]);
  const made = buildMirrorMime(sample({ originalBytes }));
  assert.deepEqual(extractOriginalEml(Buffer.from(attachmentBase64(made.mime).replace(/\s/g, ''), 'base64')), originalBytes);
  assert.deepEqual(Buffer.from(JSON.parse(made.payload).raw, 'base64url'), made.mime);
});

test('attachment uses ZIP and valid folded base64, without inline RFC MIME', () => {
  const made = buildMirrorMime(sample({ originalBytes: Buffer.alloc(2048, 137) }));
  assert.ok(made.mime.toString().includes('Content-Disposition: attachment; filename="original.zip"'));
  assert.equal(made.mime.toString().includes('Content-Type: message/rfc822'), false);
  for (const line of attachmentBase64(made.mime).split('\r\n')) {
    assert.ok(line.length <= 76);
    assert.match(line, /^[A-Za-z0-9+/]+={0,2}$/);
  }
});

test('header newline and NUL injection are rejected', () => {
  for (const field of ['sender', 'subject', 'rfcId']) {
    for (const injected of ['value\r\nBcc: other@example.test', 'value\nBcc: other@example.test', 'value\u0000']) {
      assert.throws(() => buildMirrorMime(sample({ [field]: injected })), /header/);
    }
  }
  assert.throws(() => buildMirrorMime(sample({ labels: ['01JD\r\nBcc: other@example.test'] })), /labels/);
});

test('missing or non-text headers and malformed optional body fields are rejected', () => {
  for (const field of ['sender', 'subject', 'rfcId']) {
    for (const value of [null, undefined, 42, {}]) assert.throws(() => buildMirrorMime(sample({ [field]: value })), /header/);
  }
  for (const field of ['note', 'originalHtml', 'originalText']) {
    for (const value of [null, 42, {}]) assert.throws(() => buildMirrorMime(sample({ [field]: value })), /body text/);
  }
  const options = sample();
  delete options.note; delete options.originalHtml; delete options.originalText;
  assert.ok(buildMirrorMime(options).mime.length > 0);
});

test('empty RFC bytes are refused', () => {
  assert.throws(() => buildMirrorMime(sample({ originalBytes: Buffer.alloc(0) })), /empty/);
  assert.throws(() => buildMirrorMime(sample({ originalBytes: '' })), /empty/);
});

test('20 MiB limit covers source and final base64 JSON transport expansion', () => {
  assert.throws(() => buildMirrorMime(sample({ originalBytes: Buffer.alloc(MAX_TRANSPORT_BYTES + 1) })), /20 MiB/);
  assert.throws(() => buildMirrorMime(sample({ originalBytes: Buffer.alloc(12 * 1024 * 1024) })), /20 MiB/);
});

test('UTF-8 subject is lossless and long RFC 2047 encoded words remain within limits', () => {
  const subject = '합성 제목 🧪 '.repeat(25);
  const made = buildMirrorMime(sample({ subject }));
  const headers = made.mime.toString().split('\r\n\r\n', 1)[0];
  const encoded = headers.match(/Subject: ([\s\S]*?)\r\nDate:/)[1];
  const words = [...encoded.matchAll(/=\?UTF-8\?B\?([A-Za-z0-9+/=]+)\?=/g)];
  assert.ok(words.length > 1);
  assert.ok(words.every(word => word[0].length <= 75));
  assert.equal(words.map(word => Buffer.from(word[1], 'base64').toString('utf8')).join(''), `${MIRROR_MARKER} ${subject}`);
});

test('body contains mirror metadata and supplied HTML in encoded alternatives', () => {
  const made = buildMirrorMime(sample());
  const parts = [...made.mime.toString().matchAll(/Content-Type: text\/(plain|html); charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n([A-Za-z0-9+/=\r\n]+?)\r\n--/g)];
  assert.equal(parts.length, 2);
  const decoded = parts.map(part => Buffer.from(part[2].replace(/\s/g, ''), 'base64').toString('utf8'));
  for (const body of decoded) {
    assert.ok(body.includes(MIRROR_MARKER));
    assert.ok(body.includes(`Operation: ${'a'.repeat(64)}`));
    assert.ok(body.includes('Canonical-Labels: 01JD'));
  }
  assert.ok(decoded[1].includes('<div>Synthetic original</div>'));
  assert.ok(decoded[1].includes('original.zip'));
  assert.ok(decoded[1].includes(`Original-EML-SHA256: ${made.originalSha256}`));
});

test('deterministic ZIP interoperates with Python zipfile and preserves the single entry', () => {
  const original = sample().originalBytes;
  const zip = buildOriginalZip(original);
  assert.deepEqual(zip, buildOriginalZip(original));
  const code = 'import sys,io,zipfile,hashlib,json\nz=zipfile.ZipFile(io.BytesIO(sys.stdin.buffer.read()))\nassert z.namelist()==["original.eml"]\nassert z.getinfo("original.eml").compress_type==zipfile.ZIP_STORED\nassert z.testzip() is None\nprint(hashlib.sha256(z.read("original.eml")).hexdigest())';
  const hash = execFileSync('python3', ['-c', code], { input: zip, encoding: 'utf8' }).trim();
  assert.equal(hash, buildMirrorMime(sample()).originalSha256);
});

test('ZIP corruption, duplicate entries, traversal names, and trailing data are refused', () => {
  const zip = buildOriginalZip(sample().originalBytes);
  const corrupt = Buffer.from(zip); corrupt[45] ^= 1;
  assert.throws(() => extractOriginalEml(corrupt), /Invalid original ZIP/);
  const duplicate = Buffer.from(zip); duplicate.writeUInt16LE(2, duplicate.length - 12);
  assert.throws(() => extractOriginalEml(duplicate), /Invalid original ZIP/);
  const traversal = Buffer.from(zip); traversal.write('../evil.eml', 30);
  assert.throws(() => extractOriginalEml(traversal), /Invalid original ZIP/);
  assert.throws(() => extractOriginalEml(Buffer.concat([zip, Buffer.from('extra')])), /Invalid original ZIP/);
});
