import { test, expect } from "@playwright/test";

// Критический поток: создать цель → запустить разведку в scope → увидеть задачу.
// Требует поднятого стека (--profile core). BASE_URL берётся из playwright.config.

test("дашборд загружается", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Обзор платформы/ })).toBeVisible();
});

test("создание цели и запуск разведки", async ({ page }) => {
  await page.goto("/targets");
  await page.getByLabel("Название").fill("E2E Target");
  await page.getByLabel("Домены (scope)").fill("example.com");
  await page.getByRole("button", { name: /Создать цель/ }).click();
  await expect(page.getByRole("heading", { name: "E2E Target" })).toBeVisible();

  await page.goto("/recon");
  await page.getByLabel("Цель").selectOption({ label: "E2E Target" });
  await page.getByLabel("Инструмент").selectOption("theharvester");
  await page.getByLabel(/Значение/).fill("example.com");
  await page.getByRole("button", { name: /Запустить/ }).click();
  await expect(page.getByText(/в очередь/)).toBeVisible();
});

test("скан вне scope блокируется", async ({ page }) => {
  await page.goto("/recon");
  await page.getByLabel("Цель").selectOption({ label: "E2E Target" });
  await page.getByLabel(/Значение/).fill("evil-not-in-scope.com");
  await page.getByRole("button", { name: /Запустить/ }).click();
  await expect(page.getByText(/scope/i)).toBeVisible();
});
