import { expect, test } from "@playwright/test";

const ADMIN_USER = "admin";
// Definida pelo playwright.config.js (E2E_ADMIN_PASSWORD), a mesma usada para criar o admin do banco de teste.
const ADMIN_PASS = process.env.E2E_ADMIN_PASSWORD;

function uniqueName(prefix) {
  return `${prefix}-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
}

async function login(page) {
  await page.goto("/login");
  await page.getByLabel("Usuário").fill(ADMIN_USER);
  await page.getByLabel("Senha").fill(ADMIN_PASS);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
}

async function selectOption(page, label, optionText) {
  await page.getByRole("combobox", { name: label }).click();
  await page.getByRole("option", { name: optionText, exact: true }).click();
}

async function selectFirstOption(page, label) {
  await page.getByRole("combobox", { name: label }).click();
  const option = page.getByRole("option").first();
  const value = (await option.textContent())?.trim() || "";
  await option.click();
  return value;
}

test("faz login e abre o dashboard", async ({ page }) => {
  await login(page);
  await expect(page.getByText("Visão geral do negócio")).toBeVisible();
});

test("gerencia item de estoque pela interface", async ({ page }) => {
  const descricao = uniqueName("peca-e2e");

  await login(page);
  await page.getByRole("link", { name: "Estoque" }).click();
  await page.getByRole("button", { name: /Nova Peça/i }).click();
  await page.getByLabel("Descrição *").fill(descricao);
  await selectOption(page, "Modelo compatível", "Universal (serve para qualquer modelo)");
  await page.getByLabel("Fornecedor").fill("Fornecedor E2E");
  await page.getByLabel("Valor (R$)").fill("12.34");
  await page.getByLabel("Quantidade").fill("2");
  await page.getByLabel("Data de Compra").fill("2026-04-11");
  await page.getByTestId("stock-save-button").click();
  await expect(page.getByRole("dialog")).not.toBeVisible();

  await page.getByPlaceholder("Buscar peça...").fill(descricao);
  const row = page.locator('[data-testid^="stock-row-"]', { hasText: descricao }).first();
  await expect.poll(async () => row.count()).toBe(1);
  await expect(row).toBeVisible();
  await row.getByRole("button", { name: /Editar peça/ }).click();
  const quantidadeInput = page.getByLabel("Quantidade");
  await quantidadeInput.fill("5");
  await page.getByTestId("stock-save-button").click();
  await expect(page.getByText("Item atualizado!")).toBeVisible();

  await row.getByRole("button", { name: /Excluir peça/ }).click();
  await page.getByRole("button", { name: "Excluir" }).click();
  await expect(page.getByText("Item excluído")).toBeVisible();
});

test("cria, edita e exclui uma ordem de serviço", async ({ page }) => {
  const cliente = uniqueName("cliente-e2e");
  const clienteEditado = `${cliente}-editado`;

  await login(page);
  await page.getByRole("link", { name: "Ordens de Serviço" }).click();
  await page.getByRole("link", { name: /Nova OS/i }).click();

  await page.getByLabel("Nome do Cliente *").fill(cliente);
  await selectFirstOption(page, "Modelo");
  if (await page.getByRole("combobox", { name: "Cor" }).isVisible()) {
    const corBox = page.getByRole("combobox", { name: "Cor" });
    if ((await corBox.textContent())?.trim() === "") {
      await selectFirstOption(page, "Cor");
    } else {
      await selectFirstOption(page, "Cor");
    }
  }
  await selectFirstOption(page, "Técnico");
  await selectFirstOption(page, "Vendedor");
  await page.getByRole("checkbox").first().click();
  await page.getByLabel("Valor Cobrado (R$)").fill("150");
  await page.getByTestId("order-create-button").click();
  await expect(page.getByText("Ordem criada com sucesso!")).toBeVisible();

  await page.getByPlaceholder("Buscar cliente, modelo, IMEI...").fill(cliente);
  const row = page.locator('[data-testid^="order-row-"]', { hasText: cliente }).first();
  await expect(row).toBeVisible();
  await row.getByRole("button", { name: /Editar ordem/ }).click();

  await page.getByLabel("Nome do Cliente *").fill(clienteEditado);
  await page.getByTestId("order-save-button").click();
  await expect(page.getByText("Ordem atualizada!")).toBeVisible();

  await page.getByPlaceholder("Buscar cliente, modelo, IMEI...").fill(clienteEditado);
  const editedRow = page.locator('[data-testid^="order-row-"]', { hasText: clienteEditado }).first();
  await expect(editedRow).toBeVisible();
  await editedRow.getByRole("button", { name: /Excluir ordem/ }).click();
  await page.getByRole("button", { name: "Excluir" }).click();
  await expect(page.getByText("Ordem excluída")).toBeVisible();
});

test("cria backup e gerencia usuário pela interface", async ({ page }) => {
  const username = uniqueName("user").toLowerCase();

  await login(page);
  await page.getByRole("link", { name: "Backups" }).click();
  await page.waitForFunction(() => {
    const hasRow = !!document.querySelector("tbody tr");
    const emptyState = document.body.innerText.includes("Nenhum backup encontrado.");
    return hasRow || emptyState;
  });
  const rowsBefore = await page.locator("tbody tr").count();
  const firstBackupName = rowsBefore > 0
    ? await page.locator("tbody tr").first().locator("td").first().textContent()
    : null;
  await page.getByRole("button", { name: /Criar backup/i }).click();
  if (rowsBefore === 0) {
    await expect.poll(async () => page.locator("tbody tr").count()).toBe(1);
  } else {
    await expect
      .poll(async () => page.locator("tbody tr").first().locator("td").first().textContent())
      .not.toBe(firstBackupName);
  }

  await page.getByRole("link", { name: "Usuários" }).click();
  await page.getByRole("button", { name: /Novo Usuário/i }).click();
  await page.getByLabel("Nome *").fill("Usuario E2E");
  await page.getByLabel("Usuário *").fill(username);
  await page.getByLabel("Senha *").fill("SenhaE2E123!");
  await selectOption(page, "Perfil", "vendedor");
  await page.getByTestId("users-save-button").click();
  await expect(page.getByText("Usuário criado!")).toBeVisible();

  const row = page.locator('[data-testid^="user-row-"]', { hasText: username }).first();
  await expect(row).toBeVisible();
  await row.getByRole("button", { name: /Excluir usuário/ }).click();
  await page.getByRole("button", { name: "Excluir" }).click();
  await expect(page.getByText("Usuário excluído")).toBeVisible();
});
