import { useNavigate } from "react-router-dom";
import logoFull from "../assets/logo-full.png";
import logoIcon from "../assets/logo-icon.png";

interface BuildingArtProps {
  className?: string;
  rows?: number;
  cols?: number;
}

// Silhueta de prédio à noite, gerada em CSS (sem depender de foto externa) -
// janelas acesas em posição determinística (seed fixa) para não "piscar"
// entre renders.
function BuildingArt({ className = "", rows = 12, cols = 10 }: BuildingArtProps) {
  const total = rows * cols;
  const janelas = Array.from({ length: total }, (_, i) => {
    const seed = (i * 37 + 11) % 97;
    if (seed < 78) return "unlit";
    if (seed < 90) return "dim";
    return "lit";
  });

  return (
    <div className={`relative overflow-hidden bg-gradient-to-br from-[#060a1f] via-[#0b1638] to-[#13214f] ${className}`}>
      <div
        className="grid h-full w-full gap-[4px] p-4"
        style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}
      >
        {janelas.map((estado, i) => (
          <div
            key={i}
            className={
              estado === "lit"
                ? "rounded-[1px] bg-amber-200/85"
                : estado === "dim"
                  ? "rounded-[1px] bg-brand-300/30"
                  : "rounded-[1px] bg-white/[0.04]"
            }
          />
        ))}
      </div>
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-ink/90 via-ink/10 to-transparent" />
    </div>
  );
}

const RECURSOS = [
  {
    icone: (
      <path
        d="M3 3v18h18M8 17V11m5 6V7m5 10v-4"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    ),
    titulo: "Dashboard Inteligente",
    descricao: "Gráficos, indicadores e informações do prédio atualizadas em uma visão simples e objetiva.",
  },
  {
    icone: (
      <path
        d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    ),
    titulo: "Avisos e Comunicação",
    descricao: "Compartilhe notificações e avisos importantes de forma rápida, direta e centralizada.",
  },
  {
    icone: (
      <path
        d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2M9 11a4 4 0 100-8 4 4 0 000 8zM23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    ),
    titulo: "Gestão de Moradores",
    descricao: "Perfis e dados de residentes organizados para uma gestão acessível e segura.",
  },
  {
    icone: (
      <path
        d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.77z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    ),
    titulo: "Serviços e Manutenção",
    descricao: "Acompanhe tarefas, prazos e checklists para manter cada atividade em dia.",
  },
  {
    icone: (
      <path
        d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    ),
    titulo: "Documentos Digitais",
    descricao: "Arquivos importantes sempre disponíveis, organizados e protegidos em um único ambiente.",
  },
];

export function LandingPage() {
  const navigate = useNavigate();

  function irParaLogin(): void {
    navigate("/login");
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Navbar */}
      <header className="sticky top-0 z-20 border-b border-slate-100 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-2">
            <img src={logoIcon} alt="" className="h-8 w-auto" />
            <span className="text-lg font-bold tracking-tight text-ink">
              Meu<span className="text-brand-600">Prédio</span>
            </span>
          </div>
          <nav className="hidden items-center gap-6 text-sm font-medium text-slate-600 md:flex">
            <a href="#recursos" className="hover:text-ink">
              Recursos
            </a>
            <a href="#como-funciona" className="hover:text-ink">
              Como funciona
            </a>
            <a href="#footer" className="hover:text-ink">
              Segurança
            </a>
          </nav>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={irParaLogin}
              className="hidden items-center gap-1.5 rounded-lg bg-ink px-3.5 py-2 text-sm font-medium text-white hover:bg-ink/90 sm:flex"
            >
              <svg viewBox="0 0 24 24" fill="none" className="h-3.5 w-3.5">
                <rect x="5" y="11" width="14" height="9" rx="2" stroke="currentColor" strokeWidth="2" />
                <path d="M8 11V7a4 4 0 018 0v4" stroke="currentColor" strokeWidth="2" />
              </svg>
              Área do cliente
            </button>
            <button
              type="button"
              onClick={irParaLogin}
              className="rounded-lg bg-brand-600 px-3.5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-brand-700"
            >
              Conhecer agora
            </button>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="bg-gradient-to-b from-brand-50/70 to-white">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-14 sm:px-6 lg:grid-cols-2 lg:items-center lg:py-20">
          <div>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-100 px-3 py-1 text-xs font-medium text-brand-700">
              <svg viewBox="0 0 24 24" fill="none" className="h-3.5 w-3.5">
                <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2" />
                <path d="M12 7v5l3 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
              Gestão condominial em um só lugar
            </span>
            <h1 className="mt-4 text-3xl font-extrabold leading-tight tracking-tight text-ink sm:text-4xl lg:text-[2.75rem]">
              A gestão do seu prédio, mais simples e inteligente.
            </h1>
            <p className="mt-4 max-w-md text-sm leading-relaxed text-slate-500 sm:text-base">
              O Meu Prédio centraliza comunicação, moradores, serviços e documentos em um só lugar
              para uma rotina mais organizada, segura e eficiente.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={irParaLogin}
                className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white shadow-md shadow-brand-600/25 hover:bg-brand-700"
              >
                <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4">
                  <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                Conheça o Meu Prédio
              </button>
              <a
                href="#como-funciona"
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-ink hover:bg-slate-50"
              >
                <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4">
                  <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2" />
                  <path d="M10 9l5 3-5 3V9z" fill="currentColor" />
                </svg>
                Ver como funciona
              </a>
            </div>
          </div>

          <div className="relative">
            <BuildingArt className="aspect-[4/3] w-full rounded-2xl shadow-xl" rows={14} cols={12} />
            <div className="absolute bottom-4 left-4 flex items-center gap-2 rounded-full bg-white/95 px-3 py-1.5 text-xs font-medium text-slate-700 shadow-lg backdrop-blur">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
              </span>
              Seu condomínio conectado
            </div>
          </div>
        </div>
      </section>

      {/* Recursos */}
      <section id="recursos" className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <p className="text-xs font-semibold uppercase tracking-wider text-brand-600">Recursos essenciais</p>
        <h2 className="mt-2 text-2xl font-bold text-ink sm:text-3xl">
          Tudo organizado para a rotina fluir melhor.
        </h2>
        <p className="mt-2 max-w-xl text-sm text-slate-500 sm:text-base">
          Uma experiência digital clara para administradores, síndicos e moradores acompanharem o
          que importa.
        </p>

        <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {RECURSOS.map((recurso) => (
            <div key={recurso.titulo} className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-100">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5">
                  {recurso.icone}
                </svg>
              </div>
              <h3 className="mt-3 text-sm font-semibold text-ink">{recurso.titulo}</h3>
              <p className="mt-1 text-sm text-slate-500">{recurso.descricao}</p>
            </div>
          ))}

          <div className="relative overflow-hidden rounded-2xl shadow-sm sm:col-span-2 lg:col-span-1">
            <BuildingArt className="h-full min-h-[220px] w-full" rows={16} cols={8} />
            <div className="absolute inset-x-0 bottom-0 p-5">
              <p className="text-sm font-semibold text-white">Prédio em destaque</p>
              <p className="mt-1 text-xs text-white/80">
                Mais visibilidade para uma gestão que aproxima todo o condomínio.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Visão unificada */}
      <section id="como-funciona" className="bg-brand-50/50 py-16">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 sm:px-6 lg:grid-cols-2 lg:items-center">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-brand-600">Visão unificada</p>
            <h2 className="mt-2 text-2xl font-bold text-ink sm:text-3xl">
              Tenha o controle do seu prédio em poucos cliques.
            </h2>
            <p className="mt-3 max-w-md text-sm text-slate-500 sm:text-base">
              Uma visão geral feita para tomar decisões com mais agilidade, sem perder o contexto
              da operação.
            </p>
            <p className="mt-4 flex items-center gap-2 text-sm font-medium text-ink">
              <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-600 text-white">
                <svg viewBox="0 0 24 24" fill="none" className="h-3 w-3">
                  <path d="M20 6L9 17l-5-5" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </span>
              Informações claras para agir no momento certo.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-100 bg-white p-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <img src={logoIcon} alt="" className="h-6 w-auto" />
                <span className="text-sm font-bold text-ink">Meu Prédio</span>
              </div>
              <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4 text-slate-400">
                <path
                  d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>

            <div className="mt-3 grid grid-cols-3 gap-2">
              <div className="rounded-xl bg-slate-50 p-2.5">
                <p className="text-[11px] text-slate-500">Moradores</p>
                <p className="text-lg font-bold text-ink">128</p>
                <p className="text-[10px] text-emerald-600">Ativos</p>
              </div>
              <div className="rounded-xl bg-slate-50 p-2.5">
                <p className="text-[11px] text-slate-500">Manutenções</p>
                <p className="text-lg font-bold text-ink">06</p>
                <p className="text-[10px] text-amber-600">Em andamento</p>
              </div>
              <div className="rounded-xl bg-slate-50 p-2.5">
                <p className="text-[11px] text-slate-500">Documentos</p>
                <p className="text-lg font-bold text-ink">24</p>
                <p className="text-[10px] text-brand-600">Organizados</p>
              </div>
            </div>

            <div className="mt-3 rounded-xl bg-slate-50 p-3">
              <p className="text-[11px] font-medium text-slate-500">Atividade do condomínio</p>
              <div className="mt-2 flex h-14 items-end gap-1.5">
                {[40, 55, 90, 60, 75, 95, 70].map((altura, i) => (
                  <div
                    key={i}
                    className={`w-full rounded-t-sm ${i % 2 === 0 ? "bg-brand-200" : "bg-brand-600"}`}
                    style={{ height: `${altura}%` }}
                  />
                ))}
              </div>
            </div>

            <div className="mt-3 grid grid-cols-2 gap-2">
              <div className="rounded-xl bg-slate-50 p-3">
                <p className="text-[11px] font-medium text-slate-500">Avisos recentes</p>
                <ul className="mt-1.5 space-y-1 text-[11px] text-slate-600">
                  <li>• Limpeza da garagem</li>
                  <li>• Reunião confirmada</li>
                </ul>
              </div>
              <div className="rounded-xl bg-slate-50 p-3">
                <p className="text-[11px] font-medium text-slate-500">Moradores</p>
                <ul className="mt-1.5 space-y-1 text-[11px] text-slate-600">
                  <li>• Novos acessos hoje</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA final */}
      <section className="px-4 py-16 sm:px-6">
        <div className="mx-auto max-w-5xl rounded-3xl bg-ink px-6 py-14 text-center shadow-xl sm:px-12">
          <p className="text-xs font-semibold uppercase tracking-wider text-brand-300">
            Simplifique a gestão
          </p>
          <h2 className="mx-auto mt-3 max-w-2xl text-2xl font-bold text-white sm:text-3xl">
            Tudo o que o seu prédio precisa, em um só lugar.
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-sm text-slate-300 sm:text-base">
            Organize a rotina, mantenha todos informados e tenha uma gestão mais tranquila todos os
            dias.
          </p>
          <button
            type="button"
            onClick={irParaLogin}
            className="mt-6 inline-flex items-center gap-1.5 rounded-lg bg-white px-5 py-2.5 text-sm font-semibold text-ink hover:bg-slate-100"
          >
            <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4">
              <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Começar agora
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer id="footer" className="border-t border-slate-100 px-4 py-8 sm:px-6">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-2">
            <img src={logoFull} alt="Meu Prédio" className="h-8 w-auto" />
          </div>
          <nav className="flex items-center gap-5 text-sm font-medium text-slate-600">
            <a href="#recursos" className="hover:text-ink">
              Recursos
            </a>
            <span className="hover:text-ink">Segurança</span>
            <span className="hover:text-ink">Suporte</span>
          </nav>
          <p className="text-xs text-slate-400">Produto digital para uma gestão condominial mais simples.</p>
        </div>
      </footer>
    </div>
  );
}
