import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { Plus } from "@phosphor-icons/react";
import { ordens as ordensApi, constantes as constApi } from "@/api/client";
import { Button } from "@/components/ui/button";
import { ListSkeleton } from "@/components/ui/loading-state";
import { ErrorState } from "@/components/ui/error-state";
import { Reveal } from "@/components/ui/reveal";
import { LooseMetric } from "@/components/ui/loose-metric";
import OrderFilters from "@/components/orders/OrderFilters";
import OrderTable from "@/components/orders/OrderTable";
import { readListContext, saveListContext, useRestoreScroll } from "@/hooks/useListContext";

const NAV_CONTEXT_KEY = "ordens";
import {
  AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogFooter,
  AlertDialogTitle, AlertDialogDescription, AlertDialogAction, AlertDialogCancel,
} from "@/components/ui/alert-dialog";

function extractMeta(ordens) {
  const tecnicos = [...new Set(ordens.map((o) => o.tecnico).filter(Boolean))];
  const vendedores = [...new Set(ordens.map((o) => o.vendedor).filter(Boolean))];
  return { tecnicos, vendedores };
}

function applyFilters(ordens, filters) {
  return ordens.filter((o) => {
    if (filters.search) {
      const q = filters.search.toLowerCase();
      if (
        !o.cliente?.toLowerCase().includes(q) &&
        !o.modelo?.toLowerCase().includes(q) &&
        !o.imei?.includes(q)
      ) return false;
    }
    if (filters.status && o.status !== filters.status) return false;
    if (filters.tipo && o.tipo !== filters.tipo) return false;
    if (filters.tecnico && o.tecnico !== filters.tecnico) return false;
    if (filters.vendedor && o.vendedor !== filters.vendedor) return false;
    return true;
  });
}

export default function Orders() {
  const [ordens, setOrdens] = useState([]);
  const [loading, setLoading] = useState(true);
  // UX-001 -- restaura filtros salvos ao voltar de uma edição, se houver.
  const [filters, setFilters] = useState(() => readListContext(NAV_CONTEXT_KEY)?.filters || {});
  const [deleteId, setDeleteId] = useState(null);
  const [constants, setConstants] = useState(null);
  const [loadError, setLoadError] = useState(false);

  const fetchOrdens = async (opts = {}) => {
    const { silent = false } = opts;
    if (!silent) setLoading(true);
    try {
      const res = await ordensApi.list();
      if (res?.ok) {
        setOrdens(res.ordens || []);
        if (!silent) setLoadError(false);
      } else if (!silent) {
        toast.error("Erro ao carregar ordens");
        setLoadError(true);
      }
    } catch {
      if (!silent) {
        toast.error("Erro ao carregar ordens");
        setLoadError(true);
      }
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrdens();
    // Auto-refresh a cada 30 segundos
    const interval = setInterval(() => fetchOrdens({ silent: true }), 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    constApi.get().then((res) => {
      if (res?.ok) setConstants(res);
    });
  }, []);

  // UX-001 -- rola de volta para o item editado (ou posição salva) assim
  // que a listagem carrega.
  useRestoreScroll(NAV_CONTEXT_KEY, !loading);

  const handleEditClick = (id) => {
    saveListContext(NAV_CONTEXT_KEY, { filters, focusId: id });
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      const res = await ordensApi.delete(deleteId);
      if (res?.ok) {
        toast.success("Ordem excluída");
        setOrdens((prev) => prev.filter((o) => o.id !== deleteId));
      } else {
        toast.error(res?.erro || "Erro ao excluir ordem");
      }
    } catch {
      toast.error("Erro ao excluir ordem");
    } finally {
      setDeleteId(null);
    }
  };

  const filtered = applyFilters(ordens, filters);
  const { tecnicos, vendedores } = extractMeta(ordens);
  const abertas = ordens.filter((o) => o.status === "Em andamento" || o.status === "Aguardando peca").length;
  const finalizadas = ordens.filter((o) => o.status === "Finalizado").length;
  const atrasadas = ordens.filter((o) => o.atrasada).length;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Ordens de Serviço</h1>
          <p className="text-muted-foreground text-sm">Gerencie as ordens de serviço</p>
        </div>
        <Link to="/ordens/nova">
          <Button><Plus className="h-4 w-4 mr-2" />Nova OS</Button>
        </Link>
      </div>

      {loading ? (
        <ListSkeleton rows={6} />
      ) : loadError && ordens.length === 0 ? (
        <ErrorState
          title="Não foi possível carregar as ordens."
          onRetry={() => fetchOrdens()}
        />
      ) : (
        <Reveal className="space-y-5">
          {/* Stats bar -- contadores soltos, sem elemento dominante (tela de CRUD simples) */}
          <div className="grid grid-cols-3 gap-x-6 gap-y-4">
            <LooseMetric label="Total" value={ordens.length} />
            <LooseMetric label="Em aberto" value={abertas} valueClassName="text-warning" />
            <LooseMetric label="Finalizadas" value={finalizadas} valueClassName="text-success" />
            {atrasadas > 0 && <LooseMetric label="Atrasadas" value={atrasadas} valueClassName="text-destructive" />}
          </div>

          <OrderFilters filters={filters} setFilters={setFilters} tecnicos={tecnicos} vendedores={vendedores} constants={constants} />

          <OrderTable orders={filtered} onDelete={setDeleteId} onEditClick={handleEditClick} />
        </Reveal>
      )}

      <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir Ordem?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta ação não pode ser desfeita. A ordem e todas suas informações serão removidas permanentemente.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
