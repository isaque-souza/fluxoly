import { Link } from "react-router-dom";
import { Pencil, Trash } from "@phosphor-icons/react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { DataTable } from "@/components/ui/data-table";
import OrderStatusBadge from "./OrderStatusBadge";
import { formatCurrency, getOrderDisplayNumber } from "@/lib/constants";

const columns = [
  {
    key: "id",
    header: "#ID",
    className: "font-mono text-xs text-muted-foreground",
    render: (os) => `#${getOrderDisplayNumber(os)}`,
  },
  {
    key: "cliente",
    header: "Cliente",
    className: "font-medium text-card-foreground max-w-[140px] truncate",
  },
  {
    key: "modelo",
    header: "Modelo / Cor",
    className: "text-muted-foreground",
    render: (os) => (
      <>
        <span className="block">{os.modelo}</span>
        {os.cor && <span className="text-xs">{os.cor}</span>}
      </>
    ),
  },
  {
    key: "tecnico",
    header: "Técnico",
    className: "text-muted-foreground",
    render: (os) => os.tecnico || "—",
  },
  {
    key: "status",
    header: "Status",
    render: (os) => <OrderStatusBadge status={os.status} />,
  },
  {
    key: "data_os",
    header: "Data",
    className: "text-muted-foreground whitespace-nowrap",
    render: (os) => (os.data_os ? new Date(os.data_os).toLocaleDateString("pt-BR") : "—"),
  },
  {
    key: "valor",
    header: "Valor",
    className: "text-card-foreground font-medium whitespace-nowrap",
    // KI-059: mesmo valor do backend (`faturamento`) -- o Valor com Desconto vale quando preenchido.
    render: (os) => formatCurrency(os.faturamento ?? (os.valor_descontado || os.valor_cobrado || 0)),
  },
];

export default function OrderTable({ orders = [], onDelete, onEditClick }) {
  if (orders.length === 0) {
    return (
      <EmptyState
        title="Nenhuma ordem encontrada"
        description="Ajuste os filtros ou crie uma nova ordem de serviço."
      />
    );
  }

  const columnsWithActions = [
    ...columns,
    {
      key: "acoes",
      header: "",
      render: (os) => (
        <div className="flex items-center gap-1 justify-end">
          <Link to={`/ordens/editar/${os.id}`} onClick={() => onEditClick?.(os.id)}>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              aria-label={`Editar ordem ${getOrderDisplayNumber(os)}`}
            >
              <Pencil className="h-3.5 w-3.5" />
            </Button>
          </Link>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 text-destructive hover:text-destructive"
            aria-label={`Excluir ordem ${getOrderDisplayNumber(os)}`}
            onClick={() => onDelete?.(os.id)}
          >
            <Trash className="h-3.5 w-3.5" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <DataTable
      columns={columnsWithActions}
      rows={orders}
      getRowKey={(os) => os.id}
      getRowProps={(os) => ({ "data-testid": `order-row-${os.id}`, "data-context-row": os.id })}
    />
  );
}
