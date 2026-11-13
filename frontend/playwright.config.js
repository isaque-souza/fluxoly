import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "@playwright/test";

// KI-068: mesma topologia da produção — SPA na raiz (vite preview do build, como na Vercel) e API Flask
// separada, alcançada pelo proxy /api do vite.config.js. Sem PowerShell: roda em macOS, Linux e Windows.

const FRONTEND_DIR = path.dirname(fileURLToPath(import.meta.url));
const REPO_DIR = path.resolve(FRONTEND_DIR, "..");
const BACKEND_PORT = 5080; // alvo do proxy /api em vite.config.js
const FRONTEND_PORT = Number(process.env.E2E_FRONTEND_PORT || 4173);

// O build testado precisa falar com o backend local. Um VITE_API_URL (ambiente ou .env*) mandaria as
// requisições para outra API — possivelmente a de produção.
const ENV_FILES = [".env", ".env.local", ".env.production", ".env.production.local"];
const apiExterna =
  process.env.VITE_API_URL ||
  ENV_FILES.some((nome) => {
    const arquivo = path.join(FRONTEND_DIR, nome);
    return fs.existsSync(arquivo) && /^\s*VITE_API_URL\s*=\s*\S/m.test(fs.readFileSync(arquivo, "utf8"));
  });
if (apiExterna) {
  throw new Error("E2E: remova VITE_API_URL (ambiente ou frontend/.env*) — os testes usam só o backend local.");
}

// Banco descartável por execução. A variável é herdada pelos processos de worker, que recarregam este
// arquivo, então todos enxergam o mesmo diretório.
if (!process.env.E2E_DATA_DIR) {
  process.env.E2E_DATA_DIR = fs.mkdtempSync(path.join(os.tmpdir(), "fluxoly-e2e-"));
}
process.env.E2E_ADMIN_PASSWORD ||= "e2e-admin-senha";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  use: {
    baseURL: `http://127.0.0.1:${FRONTEND_PORT}`,
    headless: true,
  },
  webServer: [
    {
      command: `${process.env.E2E_PYTHON || (process.platform === "win32" ? "python" : "python3")} app.py`,
      cwd: REPO_DIR,
      url: `http://127.0.0.1:${BACKEND_PORT}/health`,
      env: {
        IR_FLOW_DATA_DIR: process.env.E2E_DATA_DIR,
        IR_FLOW_HOST: "127.0.0.1",
        IR_FLOW_PORT: String(BACKEND_PORT),
        IR_FLOW_NO_BROWSER: "1",
        IR_FLOW_ENABLE_BACKGROUND_JOBS: "0",
        MERCADO_PHONE_INTEGRATION_ENABLED: "0",
        FLASK_SECRET_KEY: "e2e-somente-teste",
        IR_FLOW_ADMIN_PASSWORD: process.env.E2E_ADMIN_PASSWORD,
      },
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: `npx vite preview --host 127.0.0.1 --port ${FRONTEND_PORT} --strictPort`,
      cwd: FRONTEND_DIR,
      url: `http://127.0.0.1:${FRONTEND_PORT}/`,
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
});
