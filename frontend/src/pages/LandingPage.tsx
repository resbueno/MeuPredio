import { lazy, Suspense, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import logoFull from "../assets/logo-full.png";
import logoIcon from "../assets/logo-icon.png";
import fotoHero from "../assets/landing-hero.jpg";
import { enviarContato } from "../api/contato";

// Prévia carregada sob demanda: traz junto as páginas reais + o backend falso.
const DemoTour = lazy(() =>
  import("../components/landing/DemoTour").then((m) => ({ default: m.DemoTour }))
);

const RECURSOS = [
  {
    icone: <path d="M18 20V10M12 20V4M6 20v-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />,
    titulo: "Portal da Transparência",
    descricao: "Balancete, gráficos por categoria e prévia da conta de cada unidade, sempre à vista de todos.",
  },
  {
    icone: (
      <path
        d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    ),
    titulo: "Boletos e Contas Recorrentes",
    descricao: "Leitura automática de boletos por IA, rateio entre unidades e contas mensais geradas sozinhas.",
  },
  {
    icone: (
      <path
        d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    ),
    titulo: "Avisos e Ocorrências",
    descricao: "Avisos gerais, avisos diretos por unidade e livro de ocorrências, tudo em um só lugar.",
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
    titulo: "Sino de Notificações",
    descricao: "Um alerta só, para avisos, ocorrências, reuniões e entregas - sem precisar caçar informação.",
  },
  {
    icone: (
      <path
        d="M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V6a2 2 0 012-2z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    ),
    titulo: "Reuniões Digitais",
    descricao: "Convocação, pauta, confirmação de presença por unidade e ata registrada no sistema.",
  },
  {
    icone: (
      <path
        d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0zM12 13a3 3 0 100-6 3 3 0 000 6z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    ),
    titulo: "Reserva de Espaços",
    descricao: "Síndico libera a agenda do salão e áreas comuns; moradores reservam a data direto pelo sistema.",
  },
  {
    icone: (
      <path
        d="M20.5 7.3L12 12l-8.5-4.7M12 12v10M3.3 7.3L12 2l8.7 5.3v9.4L12 22l-8.7-5.3V7.3z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    ),
    titulo: "Portaria Digital",
    descricao: "Registro de visitantes (com veículo) e de encomendas recebidas, visível para zelador e síndico.",
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
    titulo: "Moradores e Unidades",
    descricao: "Um login pode acumular papéis, cadastro de veículos e vaga, tudo vinculado à unidade certa.",
  },
];

export function LandingPage() {
  const navigate = useNavigate();
  const [mostrarDemo, setMostrarDemo] = useState(false);
  const [mostrarFormularioContato, setMostrarFormularioContato] = useState(false);
  const [contatoEnviado, setContatoEnviado] = useState(false);
  const [contatoErro, setContatoErro] = useState(false);
  const [contatoEnviando, setContatoEnviando] = useState(false);
  const [contatoForm, setContatoForm] = useState({ nome: "", email: "", telefone: "", mensagem: "" });

  function irParaLogin(): void {
    navigate("/login");
  }

  async function onSubmitContato(event: FormEvent): Promise<void> {
    event.preventDefault();
    setContatoErro(false);
    setContatoEnviando(true);
    try {
      await enviarContato({
        nome: contatoForm.nome,
        email: contatoForm.email,
        telefone: contatoForm.telefone || undefined,
        mensagem: contatoForm.mensagem || undefined,
      });
      setContatoEnviado(true);
    } catch {
      setContatoErro(true);
    } finally {
      setContatoEnviando(false);
    }
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
              onClick={() => setMostrarDemo(true)}
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
              Portal da transparência, boletos com leitura por IA, avisos, reuniões digitais,
              reserva de espaços e portaria com controle de visitantes - tudo em um só sistema,
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
            <img
              src={fotoHero}
              alt="Fachada de um condomínio residencial à noite, com janelas acesas"
              className="aspect-[4/3] w-full rounded-2xl object-cover shadow-xl"
            />
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
        </div>

        <p className="mt-8 text-center text-sm font-medium text-slate-500">
          Feito para condomínios de qualquer porte — de pequenos prédios residenciais a médios e
          grandes complexos.
        </p>
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
                <p className="text-[11px] text-slate-500">Reservas</p>
                <p className="text-lg font-bold text-ink">05</p>
                <p className="text-[10px] text-brand-600">Este mês</p>
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
                <p className="text-[11px] font-medium text-slate-500">Portaria</p>
                <ul className="mt-1.5 space-y-1 text-[11px] text-slate-600">
                  <li>• 2 visitantes hoje</li>
                  <li>• 1 encomenda recebida</li>
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
          {!mostrarFormularioContato && (
            <button
              type="button"
              onClick={() => setMostrarFormularioContato(true)}
              className="mt-6 inline-flex items-center gap-1.5 rounded-lg bg-white px-5 py-2.5 text-sm font-semibold text-ink hover:bg-slate-100"
            >
              <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4">
                <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              Começar agora
            </button>
          )}

          {mostrarFormularioContato && !contatoEnviado && (
            <form onSubmit={onSubmitContato} className="mx-auto mt-6 max-w-md space-y-3 text-left" noValidate>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <input
                  required
                  placeholder="Seu nome"
                  value={contatoForm.nome}
                  onChange={(event) => setContatoForm((f) => ({ ...f, nome: event.target.value }))}
                  className="w-full rounded-lg border border-white/20 bg-white/10 px-3 py-2 text-sm text-white placeholder:text-slate-400 focus:border-white/40 focus:outline-none"
                />
                <input
                  required
                  type="email"
                  placeholder="Seu e-mail"
                  value={contatoForm.email}
                  onChange={(event) => setContatoForm((f) => ({ ...f, email: event.target.value }))}
                  className="w-full rounded-lg border border-white/20 bg-white/10 px-3 py-2 text-sm text-white placeholder:text-slate-400 focus:border-white/40 focus:outline-none"
                />
              </div>
              <input
                placeholder="Telefone (opcional)"
                value={contatoForm.telefone}
                onChange={(event) => setContatoForm((f) => ({ ...f, telefone: event.target.value }))}
                className="w-full rounded-lg border border-white/20 bg-white/10 px-3 py-2 text-sm text-white placeholder:text-slate-400 focus:border-white/40 focus:outline-none"
              />
              <textarea
                rows={3}
                placeholder="Conte um pouco sobre o seu condomínio (opcional)"
                value={contatoForm.mensagem}
                onChange={(event) => setContatoForm((f) => ({ ...f, mensagem: event.target.value }))}
                className="w-full rounded-lg border border-white/20 bg-white/10 px-3 py-2 text-sm text-white placeholder:text-slate-400 focus:border-white/40 focus:outline-none"
              />
              {contatoErro && (
                <p className="text-sm text-red-300">Não foi possível enviar. Tente novamente.</p>
              )}
              <div className="flex justify-center gap-2">
                <button
                  type="submit"
                  disabled={contatoEnviando}
                  className="rounded-lg bg-white px-5 py-2.5 text-sm font-semibold text-ink hover:bg-slate-100 disabled:opacity-60"
                >
                  {contatoEnviando ? "Enviando..." : "Enviar"}
                </button>
                <button
                  type="button"
                  onClick={() => setMostrarFormularioContato(false)}
                  className="rounded-lg border border-white/30 px-5 py-2.5 text-sm font-medium text-white hover:bg-white/10"
                >
                  Cancelar
                </button>
              </div>
            </form>
          )}

          {contatoEnviado && (
            <p className="mx-auto mt-6 max-w-md text-sm font-medium text-emerald-300">
              Recebemos seu contato! Em breve alguém da nossa equipe vai falar com você.
            </p>
          )}
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
            <a href="#como-funciona" className="hover:text-ink">
              Como funciona
            </a>
          </nav>
          <p className="text-xs text-slate-400">Desenvolvido por Renato Bueno - RBBrDev</p>
        </div>
      </footer>

      {mostrarDemo && (
        <Suspense fallback={null}>
          <DemoTour onClose={() => setMostrarDemo(false)} />
        </Suspense>
      )}
    </div>
  );
}
