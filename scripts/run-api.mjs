#!/usr/bin/env node
// Cross-platform runner for services/api commands inside the virtualenv.
// Works seamlessly on Windows (.venv/Scripts) and macOS/Linux (.venv/bin).

import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const API_DIR = resolve(REPO_ROOT, "services/api");
const IS_WIN = process.platform === "win32";
const VENV_BIN_DIR = resolve(API_DIR, ".venv", IS_WIN ? "Scripts" : "bin");

const args = process.argv.slice(2);
if (args.length === 0) {
  console.error("Usage: node scripts/run-api.mjs <command> [args...]");
  process.exit(1);
}

const cmdName = args[0];
let restArgs = args.slice(1);

// Resolve executable path
let exePath = resolve(VENV_BIN_DIR, IS_WIN ? `${cmdName}.exe` : cmdName);

// Fallback: if .exe doesn't exist directly on Windows, check for script without .exe or run via python -m
if (IS_WIN && !existsSync(exePath)) {
  const exeNoExt = resolve(VENV_BIN_DIR, cmdName);
  if (existsSync(exeNoExt)) {
    exePath = exeNoExt;
  } else {
    // Run via python -m <cmdName>
    exePath = resolve(VENV_BIN_DIR, "python.exe");
    restArgs = ["-m", cmdName, ...restArgs];
  }
}

// Ensure env has port set if uvicorn
const env = { ...process.env };
if (cmdName === "uvicorn") {
  const port = env.API_PORT || "8000";
  // Replace port placeholder if passed as an arg like --port ${API_PORT:-8000} or literal port
  restArgs = restArgs.map((arg) => (arg === "${API_PORT:-8000}" ? port : arg));
}

const child = spawn(exePath, restArgs, {
  cwd: API_DIR,
  stdio: "inherit",
  env,
  shell: false,
});

child.on("error", (err) => {
  console.error(`Failed to start ${cmdName}:`, err.message);
  process.exit(1);
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
  } else {
    process.exit(code ?? 0);
  }
});
