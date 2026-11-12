import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import OrderAtrasadaBadge, { formatPrevisao } from "./OrderAtrasadaBadge";

describe("OrderAtrasadaBadge (BR-101)", () => {
  it("mostra o selo para OS aberta atrasada, com a previsão no título", () => {
    render(<OrderAtrasadaBadge os={{ status: "Em andamento", atrasada: true, data_previsao: "2026-11-05" }} />);
    expect(screen.getByTestId("os-atrasada")).toHaveAttribute("title", "Previsão de entrega: 05/11");
  });

  it("some quando a OS foi movida para Finalizado/Cancelado ou não está atrasada", () => {
    const { rerender } = render(<OrderAtrasadaBadge os={{ status: "Finalizado", atrasada: true }} />);
    expect(screen.queryByTestId("os-atrasada")).not.toBeInTheDocument();
    rerender(<OrderAtrasadaBadge os={{ status: "Cancelado", atrasada: true }} />);
    expect(screen.queryByTestId("os-atrasada")).not.toBeInTheDocument();
    rerender(<OrderAtrasadaBadge os={{ status: "Em andamento", atrasada: false }} />);
    expect(screen.queryByTestId("os-atrasada")).not.toBeInTheDocument();
  });

  it("formatPrevisao tolera vazio", () => {
    expect(formatPrevisao("")).toBe("");
  });
});
