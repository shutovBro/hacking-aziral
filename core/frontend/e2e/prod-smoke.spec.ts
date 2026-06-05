/**
 * Прод-smoke: проверяем что все публичные модули отвечают.
 * SSO-протектед поддомены должны отдавать 200 (Authentik логин-страница)
 * или 302/301 в SSO flow — оба варианта ОК.
 *
 * Запуск:
 *   BASE_URL=https://cybersecurity.aziral.com npx playwright test e2e/prod-smoke.spec.ts
 *
 * Так же запускается из CI после деплоя.
 */
import { test, expect, request } from "@playwright/test";

interface ModuleProbe {
  readonly label: string;
  readonly url: string;
}

const ROOT = "cybersecurity.aziral.com";

const PROBES: readonly ModuleProbe[] = [
  { label: "Core (главный)",  url: `https://${ROOT}/` },
  { label: "Authentik SSO",   url: `https://auth.${ROOT}/` },
  { label: "SpiderFoot",      url: `https://spiderfoot.${ROOT}/` },
  { label: "Superset",        url: `https://superset.${ROOT}/` },
  { label: "Activepieces",    url: `https://flows.${ROOT}/` },
  { label: "Cronicle",        url: `https://cron.${ROOT}/` },
  { label: "Web Terminal",    url: `https://term.${ROOT}/` },
  { label: "Stirling-PDF",    url: `https://pdf.${ROOT}/` },
  { label: "Open WebUI",      url: `https://webui.${ROOT}/` },
  { label: "Uptime Kuma",     url: `https://uptime.${ROOT}/` },
  { label: "Sub2API",         url: `https://ai.${ROOT}/` },
  { label: "Remnawave",       url: `https://proxy.${ROOT}/` },
];

// 2xx OK; 3xx ОК (редирект в SSO); 401/403 — означает что SSO работает
// но без cookie. Все эти варианты считаем "сервис жив".
const HEALTHY_STATUSES = new Set([200, 201, 301, 302, 303, 307, 308, 401, 403]);

for (const probe of PROBES) {
  test(`smoke: ${probe.label}`, async () => {
    const ctx = await request.newContext({ ignoreHTTPSErrors: false });
    const resp = await ctx.get(probe.url, { maxRedirects: 0, timeout: 15_000 });
    expect.soft(HEALTHY_STATUSES.has(resp.status()),
      `${probe.label} HTTP ${resp.status()} (${probe.url})`).toBeTruthy();
    await ctx.dispose();
  });
}

test("smoke: core API health endpoint reachable", async () => {
  // /api/health должен ответить либо 200 (если не за SSO), либо 302/401/403 (если за SSO).
  const ctx = await request.newContext();
  const resp = await ctx.get(`https://${ROOT}/api/health`, { maxRedirects: 0, timeout: 10_000 });
  expect(HEALTHY_STATUSES.has(resp.status()),
    `/api/health HTTP ${resp.status()}`).toBeTruthy();
  await ctx.dispose();
});
