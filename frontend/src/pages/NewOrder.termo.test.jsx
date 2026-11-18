import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { toast } from "sonner";
import NewOrder from "./NewOrder";

// KI-077 / BR-105 -- Nova OS criada já como "Finalizado" exige o Termo de Garantia.
// O Select do Radix não é operável no jsdom; aqui ele vira um <select> nativo.
vi.mock("@/components/ui/select", async () => {
  const React = await vi.importActual("react");
  const Ctx = React.createContext(null);
  const Select = ({ value, onValueChange, children }) => (
    <Ctx.Provider value={{ value, onValueChange }}>{children}</Ctx.Provider>
  );
  const SelectTrigger = () => null;
  const SelectValue = () => null;
  const SelectContent = ({ children }) => {
    const ctx = React.useContext(Ctx);
    return (
      <select value={ctx.value ?? ""} onChange={(e) => ctx.onValueChange(e.target.value)}>
        <option value="">—</option>
        {children}
      </select>
    );
  };
  const SelectItem = ({ value, children }) => <option value={value}>{children}</option>;
  return { Select, SelectTrigger, SelectValue, SelectContent, SelectItem };
});

const mockCreate = vi.fn();
const mockTiposList = vi.fn();

vi.mock("@/api/client", () => ({
  constantes: { get: () => Promise.resolve({ ok: true, os_tipos: ["Assistencia"], iphone_models: [] }) },
  reparos: { list: () => Promise.resolve({ ok: true, reparos: [] }) },
  estoque: { list: () => Promise.resolve({ ok: true, items: [] }) },
  ordens: { create: (...a) => mockCreate(...a) },
  precos: { sugerir: vi.fn() },
  tiposGarantia: { list: (...a) => mockTiposList(...a) },
}));
vi.mock("sonner", () => ({ toast: { error: vi.fn(), success: vi.fn() } }));

const TERMO = { id: 7, nome: "Garantia 3 meses", duracao_meses: 3, texto: "x", ativo: true };

function selectComOpcao(texto) {
  return screen.getAllByRole("combobox").find((el) => within(el).queryByRole("option", { name: texto }));
}

async function renderEEscolherFinalizado() {
  render(<MemoryRouter><NewOrder /></MemoryRouter>);
  await screen.findByText("Nova Ordem de Serviço");
  fireEvent.change(selectComOpcao("Finalizado"), { target: { value: "Finalizado" } });
}

describe("NewOrder — OS criada já finalizada (KI-077)", () => {
  beforeEach(() => {
    mockCreate.mockReset();
    mockTiposList.mockReset();
    toast.error.mockReset();
    mockTiposList.mockResolvedValue({ ok: true, items: [TERMO] });
  });

  it("em andamento não pede termo", async () => {
    render(<MemoryRouter><NewOrder /></MemoryRouter>);
    await screen.findByText("Nova Ordem de Serviço");
    expect(screen.queryByText("Termo de Garantia *")).not.toBeInTheDocument();
    expect(mockTiposList).not.toHaveBeenCalled();
  });

  it("finalizado sem termo não envia", async () => {
    await renderEEscolherFinalizado();
    expect(await screen.findByText("Termo de Garantia *")).toBeInTheDocument();
    fireEvent.submit(screen.getByTestId("order-create-button").closest("form"));
    await waitFor(() => expect(toast.error).toHaveBeenCalledWith("Selecione o Termo de Garantia da OS."));
    expect(mockCreate).not.toHaveBeenCalled();
  });

  it("finalizado com termo envia tipo_garantia_id", async () => {
    mockCreate.mockResolvedValue({ ok: true, os_id: 1 });
    await renderEEscolherFinalizado();
    await screen.findByText("Termo de Garantia *");
    await waitFor(() => expect(selectComOpcao("Garantia 3 meses (3 meses)")).toBeTruthy());
    fireEvent.change(selectComOpcao("Garantia 3 meses (3 meses)"), { target: { value: "7" } });
    fireEvent.submit(screen.getByTestId("order-create-button").closest("form"));
    await waitFor(() => expect(mockCreate).toHaveBeenCalled());
    expect(mockCreate.mock.calls[0][0]).toMatchObject({ status: "Finalizado", tipo_garantia_id: 7 });
  });
});
