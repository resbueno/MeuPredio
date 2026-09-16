import logoFull from "../assets/logo-full.png";

/** Tela de abertura/carregamento com a marca, usada enquanto a sessão é
 * verificada (boot do app) — mesma paleta do splash nativo do PWA
 * (background_color no manifest). */
export function SplashScreen() {
  return (
    <div className="flex h-screen flex-col items-center justify-center gap-4 bg-ink px-4">
      <img
        src={logoFull}
        alt="MeuPrédio"
        className="w-48 max-w-[60vw] animate-pulse rounded-xl bg-white/95 p-4 shadow-lg sm:w-56"
      />
      <span className="text-sm font-medium text-slate-300">Carregando...</span>
    </div>
  );
}
