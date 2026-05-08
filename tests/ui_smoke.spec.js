const { test, expect } = require("@playwright/test");

const baseUrl = process.env.WBG_APP_URL || "http://127.0.0.1:8765";

test("Tacive homepage loads Notion-sourced Chinese copy and data", async ({ page }) => {
  await page.goto(`${baseUrl}/zh/`);
  await expect(page.getByRole("heading", { name: "我们不提供更多信息，我们提供更好的判断。" })).toBeVisible();
  await expect(page.getByText("Tacive 把分散的半导体产业信号")).toBeVisible();
  await expect(page.getByLabel("Database metrics").getByText("138")).toBeVisible();
  await expect(page.getByText("字段治理手册编译结果")).toBeVisible();
});

test("Tacive English view, Explorer, and company detail render real records", async ({ page }) => {
  await page.goto(`${baseUrl}/en/`);
  await expect(page.getByRole("heading", { name: "Not more information. Better judgment." })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Maintained judgment objects" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "AccoPower productized capability posture" })).toBeVisible();

  await page.getByLabel("Search companies").fill("Infineon");
  await expect(page.getByRole("button", { name: /Infineon Technologies 英飞凌/ })).toBeVisible();

  await page.getByLabel("Formal / verifiable only").check();
  await expect(page.getByText("Formal").first()).toBeVisible();
});
