import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import OrderTextosPanel from "./OrderTextosPanel";

describe("OrderTextosPanel (BR-102)", () => {
  it("mostra relato, laudo, observações e observação interna com aviso de que não sai no documento", () => {
    const setField = vi.fn();
    render(<OrderTextosPanel form={{ laudo_tecnico: "Flex rompido" }} setField={setField} />);

    expect(screen.getByLabelText("Relato do cliente")).toBeInTheDocument();
    expect(screen.getByLabelText("Laudo técnico")).toHaveValue("Flex rompido");
    expect(screen.getByLabelText("Observações")).toBeInTheDocument();
    expect(screen.getByText("Não aparece em nenhum documento entregue ao cliente.")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Observação interna"), { target: { value: "ligar após 18h" } });
    expect(setField).toHaveBeenCalledWith("observacao_interna", "ligar após 18h");
  });
});
