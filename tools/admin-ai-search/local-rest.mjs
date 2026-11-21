import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
if (!process.env.AI_SEARCH_HOST_APP) throw new Error('Existing host app required');
process.loadEnvFile(path.join(process.env.AI_SEARCH_HOST_APP,'.env.local'));
const child = spawn('python3', [path.join(path.dirname(fileURLToPath(import.meta.url)),'local-rest.py'), ...process.argv.slice(2)], { stdio: 'inherit' });
child.on('exit', code => { process.exitCode = code === null ? 1 : code; });
