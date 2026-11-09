import { createContext, useCallback, useContext, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { List, X } from "@phosphor-icons/react";
import { cn } from "@/lib/utils";
import { useIsMobile } from "@/hooks/use-mobile";
import { Button } from "@/components/ui/button";

// Versao enxuta do Sidebar do shadcn/ui: cobre exatamente o que o Shell do Fluxoly usa hoje
// (fixa no desktop, drawer no mobile) -- sem modo collapsed-para-icone, sem atalho de teclado,
// sem persistencia em cookie, que o Layout.jsx atual tambem nao tem. Adicionar depois, se um uso
// real pedir, nao especulativamente (mesmo principio ja registrado no PLAN-design-system-fase1.md).

const SidebarContext = createContext(null);

export function useSidebar() {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error("useSidebar precisa ser usado dentro de um SidebarProvider");
  }
  return context;
}

export function SidebarProvider({ children }) {
  const isMobile = useIsMobile();
  const [openMobile, setOpenMobile] = useState(false);
  const closeMobile = useCallback(() => setOpenMobile(false), []);
  const toggleMobile = useCallback(() => setOpenMobile((v) => !v), []);

  return (
    <SidebarContext.Provider value={{ isMobile, openMobile, setOpenMobile, closeMobile, toggleMobile }}>
      {children}
    </SidebarContext.Provider>
  );
}

export function SidebarTrigger({ className, ...props }) {
  const { toggleMobile } = useSidebar();
  return (
    <Button variant="ghost" size="icon" onClick={toggleMobile} className={cn("h-8 w-8", className)} {...props}>
      <List className="h-5 w-5" />
      <span className="sr-only">Abrir menu</span>
    </Button>
  );
}

const MotionDiv = motion.div;
const MotionAside = motion.aside;

export function Sidebar({ children, className }) {
  const { isMobile, openMobile, closeMobile } = useSidebar();
  const reducedMotion = useReducedMotion();

  if (!isMobile) {
    return (
      <aside
        className={cn(
          "hidden lg:flex flex-col fixed left-0 top-0 h-full w-64 bg-sidebar text-sidebar-foreground border-r border-sidebar-border z-30",
          className
        )}
      >
        {children}
      </aside>
    );
  }

  return (
    <AnimatePresence>
      {openMobile && [
        <MotionDiv
          key="sidebar-backdrop"
          className="fixed inset-0 bg-black/60 z-40"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: reducedMotion ? 0 : 0.2 }}
          onClick={closeMobile}
        />,
        <MotionAside
          key="sidebar-drawer"
          className={cn(
            "fixed left-0 top-0 h-full w-64 bg-sidebar text-sidebar-foreground border-r border-sidebar-border z-50 flex flex-col",
            className
          )}
          initial={{ x: "-100%" }}
          animate={{ x: 0 }}
          exit={{ x: "-100%" }}
          transition={reducedMotion ? { duration: 0 } : { type: "tween", ease: "easeOut", duration: 0.22 }}
        >
          <div className="absolute right-3 top-3">
            <Button variant="ghost" size="icon" onClick={closeMobile} className="h-8 w-8">
              <X className="h-4 w-4" />
              <span className="sr-only">Fechar menu</span>
            </Button>
          </div>
          {children}
        </MotionAside>,
      ]}
    </AnimatePresence>
  );
}

export function SidebarHeader({ className, ...props }) {
  return <div className={cn("px-4 py-5 border-b border-sidebar-border", className)} {...props} />;
}

export function SidebarContent({ className, ...props }) {
  return <nav className={cn("flex-1 overflow-y-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden px-2 py-3 space-y-0.5", className)} {...props} />;
}

export function SidebarFooter({ className, ...props }) {
  return <div className={cn("px-3 py-3 border-t border-sidebar-border space-y-2", className)} {...props} />;
}
