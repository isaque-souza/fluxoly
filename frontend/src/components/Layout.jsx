import { createElement } from "react";
import { Outlet, Link, useLocation, useNavigate } from "react-router-dom";
import {
  SquaresFour, ClipboardText, Package, ShoppingBag, Wrench, CurrencyDollar,
  ChartBar, Kanban, Shield, Tag, Users, SignOut, User, UserCircle, HardDrives,
  Barcode, ShoppingCart, DeviceMobile, Storefront, ListMagnifyingGlass } from "@phosphor-icons/react";
import { Button } from "@/components/ui/button";
import GlobalAlerts from "./GlobalAlerts";
import ThemeToggle from "./ThemeToggle";
import { useAuth } from "@/contexts/AuthContext";
import {
  SidebarProvider,
  Sidebar,
  SidebarTrigger,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  useSidebar,
} from "@/components/ui/sidebar";

const navSections = [
  {
    label: null, // sem rótulo -- item de topo, fora de qualquer pilar
    items: [{ path: "/", label: "Dashboard", icon: SquaresFour }],
  },
  {
    label: "Vendas",
    items: [
      { path: "/vendas", label: "Vendas", icon: ShoppingCart, perfis: ["admin", "vendedor"] },
      { path: "/precos", label: "Tabelas de Preço", icon: Tag, adminOnly: true },
    ],
  },
  {
    label: "Operação",
    items: [
      { path: "/estoque", label: "Estoque", icon: Package },
      { path: "/produtos", label: "Produtos", icon: ShoppingBag },
      { path: "/unidades-serializadas", label: "Unidades Serializadas", icon: Barcode },
      { path: "/compras-aparelhos", label: "Compras de Aparelhos", icon: DeviceMobile, perfis: ["admin", "financeiro", "vendedor"] },
      { path: "/compras", label: "Lista de Compras", icon: ClipboardText },
    ],
  },
  {
    label: "Financeiro",
    items: [
      { path: "/financeiro", label: "Financeiro", icon: CurrencyDollar, perfis: ["admin", "financeiro"] },
      { path: "/custos", label: "Custos Operacionais", icon: CurrencyDollar, adminOnly: true },
    ],
  },
  {
    label: "Relacionamento",
    items: [{ path: "/clientes", label: "Clientes", icon: UserCircle }],
  },
  {
    label: "Serviços",
    items: [
      { path: "/ordens", label: "Ordens de Serviço", icon: ClipboardText },
      { path: "/kanban", label: "Kanban", icon: Kanban },
      { path: "/garantias", label: "Garantias", icon: Shield },
      { path: "/reparos", label: "Tipos de Reparo", icon: Wrench },
      { path: "/tipos-garantia", label: "Tipos de Garantia", icon: Shield, adminOnly: true },
    ],
  },
  {
    label: "Inteligência",
    items: [{ path: "/relatorios", label: "Relatórios", icon: ChartBar, adminOnly: true }],
  },
  {
    label: "Administração",
    items: [
      { path: "/dados-loja", label: "Dados da Loja", icon: Storefront, adminOnly: true },
      { path: "/usuarios", label: "Usuários", icon: Users, adminOnly: true },
      { path: "/auditoria", label: "Auditoria", icon: ListMagnifyingGlass, perfis: ["admin", "financeiro"] },
      { path: "/backup", label: "Backups", icon: HardDrives, adminOnly: true },
    ],
  },
];

function SidebarNav({ currentPath, user }) {
  const { closeMobile } = useSidebar();

  return (
    <SidebarContent>
      {navSections.map((section) => {
        const visibleItems = section.items
          .filter((item) => !item.adminOnly || user?.perfil === "admin")
          .filter((item) => !item.perfis || item.perfis.includes(user?.perfil));

        if (visibleItems.length === 0) return null;

        return (
          <div key={section.label ?? "top"} className="space-y-1">
            {section.label && (
              <p className="px-3 pt-3 pb-1 text-xs font-medium uppercase tracking-wider text-sidebar-foreground/50">
                {section.label}
              </p>
            )}
            {visibleItems.map(({ path, label, icon }) => {
              // Prefixo só por segmento inteiro: "/compras-aparelhos" não pode acender "/compras".
              const isActive = path === "/" ? currentPath === "/" : currentPath === path || currentPath.startsWith(`${path}/`);
              return (
                <Link
                  key={path}
                  to={path}
                  onClick={closeMobile}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-sidebar-primary text-sidebar-primary-foreground"
                      : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground"
                  }`}
                >
                  {createElement(icon, { className: "h-4 w-4 shrink-0" })}
                  {label}
                </Link>
              );
            })}
          </div>
        );
      })}
    </SidebarContent>
  );
}

function SidebarUserFooter({ user, onLogout }) {
  return (
    <SidebarFooter>
      {user && (
        <div className="flex items-center gap-2 px-2 py-1.5">
          <div className="h-7 w-7 rounded-full bg-sidebar-accent flex items-center justify-center">
            <User className="h-4 w-4 text-sidebar-foreground/70" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-sidebar-foreground truncate">{user.nome || user.usuario}</p>
            <p className="text-xs text-sidebar-foreground/60 capitalize">{user.perfil}</p>
          </div>
        </div>
      )}
      <div className="flex items-center justify-between px-1">
        <span className="text-xs text-sidebar-foreground/60">v1.0.0</span>
        <div className="flex items-center gap-1">
          <GlobalAlerts />
          <ThemeToggle />
          <Button
            variant="ghost"
            size="icon"
            onClick={onLogout}
            aria-label="Sair"
            className="h-8 w-8 text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent"
          >
            <SignOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </SidebarFooter>
  );
}

function AppSidebar({ currentPath, user, onLogout }) {
  return (
    <Sidebar>
      <SidebarHeader>
        <div className="flex items-center gap-2">
          <img src="/brand/fluxoly-icon-inverted.svg" alt="" className="h-8 w-8 rounded-lg" />
          <span className="font-wordmark text-sidebar-foreground text-base">Fluxoly</span>
        </div>
      </SidebarHeader>
      <SidebarNav currentPath={currentPath} user={user} />
      <SidebarUserFooter user={user} onLogout={onLogout} />
    </Sidebar>
  );
}

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <SidebarProvider>
      <div className="flex min-h-screen bg-background">
        <AppSidebar currentPath={location.pathname} user={user} onLogout={handleLogout} />

        <div className="fixed top-0 left-0 right-0 h-14 bg-sidebar border-b border-sidebar-border flex items-center px-4 lg:hidden z-30">
          <SidebarTrigger />
          <span className="ml-3 font-wordmark text-sidebar-foreground">Fluxoly</span>
        </div>

        <main className="flex-1 lg:ml-64 pt-14 lg:pt-0 min-h-screen">
          <div className="p-4 lg:p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </SidebarProvider>
  );
}
