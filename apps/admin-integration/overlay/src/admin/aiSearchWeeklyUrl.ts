export function safeEvidenceUrl(value: unknown): string | null {
  if (typeof value !== 'string' || !URL.canParse(value)) return null;
  const url = new URL(value);
  return ['http:', 'https:'].includes(url.protocol) && !url.username && !url.password ? url.href : null;
}
