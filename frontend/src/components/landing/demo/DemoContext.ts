import { createContext, useContext } from "react";

/** Presente só dentro da prévia interativa da landing page (ver
 * components/landing/DemoTour.tsx): faz o AppShell real esconder o que não
 * existe na prévia (módulos não simulados, "Sair") sem duplicar o layout. */
export interface DemoContextValue {
  onClose: () => void;
  rotasDisponiveis: string[];
}

export const DemoContext = createContext<DemoContextValue | null>(null);

export function useDemo(): DemoContextValue | null {
  return useContext(DemoContext);
}
