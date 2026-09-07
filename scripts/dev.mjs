#!/usr/bin/env node
// Cross-platform dev runner replacing dev.sh.
// Picks a free API port, wires CORS + web-side API URL, and launches concurrently programmatically.

import concurrently from "concurrently";
import { execSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(HERE, "..");

// Pick port using pick-port.mjs
let apiPort = "8000";
try {
  const out = execSync(`node "${resolve(HERE, "pick-port.mjs")}" 8000`, {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "inherit"],
  }).trim();
  if (out) apiPort = out;
} catch (err) {
  console.error("Warning: Could not automatically pick port, defaulting to 8000:", err.message);
}

if (apiPort !== "8000") {
  console.log(`\n⚠  API on http://localhost:${apiPort} (8000 was busy)\n`);
}

const env = {
  ...process.env,
  API_PORT: apiPort,
  NEXT_PUBLIC_API_URL: `http://localhost:${apiPort}`,
  API_CORS_ORIGIN_REGEX: "^http://localhost:[0-9]+$",
};

const { result } = concurrently(
  [
    { command: "pnpm dev:web", name: "web", prefixColor: "blue", env },
    { command: "pnpm dev:api", name: "api", prefixColor: "green", env },
  ],
  {
    killOthers: ["failure"],
    cwd: REPO_ROOT,
  }
);

result.then(
  () => process.exit(0),
  () => process.exit(1)
);
