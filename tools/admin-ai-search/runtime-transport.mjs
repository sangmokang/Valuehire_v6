// Optional local runner transport only; never bundled into administrator assets.
import { readTransport } from './read-transport.mjs';
if (process.env.AI_SEARCH_DOH === '1') globalThis.fetch = readTransport;
