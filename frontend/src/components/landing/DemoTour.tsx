import { useState, type FormEvent } from "react";
import logoIcon from "../../assets/logo-icon.png";

let proximoId = 1000;
function novoId(): number {
  proximoId += 1;
  return proximoId;
}

function Tile({ label, valor, nota, cor }: { label: string; valor: string; nota: string; cor: string }) {
  return (
    <div className="rounded-xl bg-slate-50 p-2.5">
      <p className="text-[11px] text-slate-500">{label}</p>
      <p className="text-lg font-bold text-ink">{valor}</p>
      <p className={`text-[10px] ${cor}`}>{nota}</p>
    </div>
  );
}

function Lista({ titulo, itens }: { titulo: string; itens: string[] }) {
  return (
    <div className="rounded-xl bg-slate-50 p-3">
      <p className="text-[11px] font-medium text-slate-500">{titulo}</p>
      <ul className="mt-1.5 space-y-1 text-[11px] text-slate-600">
        {itens.length === 0 && <li className="text-slate-400">Nada por aqui ainda.</li>}
        {itens.map((item, i) => (
          <li key={i}>• {item}</li>
        ))}
      </ul>
    </div>
  );
}

function Badge({ texto, cor }: { texto: string; cor: string }) {
  return <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${cor}`}>{texto}</span>;
}

const campoClasse =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-brand-400 focus:outline-none";
const botaoClasse =
  "shrink-0 rounded-lg bg-brand-600 px-3 py-2 text-xs font-semibold text-white hover:bg-brand-700";

// ----- Dashboard (visão geral, alimentada pelos dados das outras abas) -----
function AbaDashboard({
  chamadosAbertos,
  totalReservas,
  avisosRecentes,
  portariaHoje,
}: {
  chamadosAbertos: number;
  totalReservas: number;
  avisosRecentes: string[];
  portariaHoje: string[];
}) {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-3 gap-2">
        <Tile label="Moradores" valor="128" nota="Vinculados" cor="text-emerald-600" />
        <Tile
          label="Manutenções"
          valor={String(chamadosAbertos).padStart(2, "0")}
          nota="Em andamento"
          cor="text-amber-600"
        />
        <Tile label="Reservas" valor={String(totalReservas).padStart(2, "0")} nota="Confirmadas" cor="text-brand-600" />
      </div>
      <div className="rounded-xl bg-slate-50 p-3">
        <p className="text-[11px] font-medium text-slate-500">Atividade financeira (6 meses)</p>
        <div className="mt-2 flex h-14 items-end gap-1.5">
          {[40, 55, 90, 60, 75, 95].map((altura, i) => (
            <div
              key={i}
              className={`w-full rounded-t-sm ${i === 5 ? "bg-brand-600" : "bg-brand-200"}`}
              style={{ height: `${altura}%` }}
            />
          ))}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <Lista titulo="Avisos recentes" itens={avisosRecentes} />
        <Lista titulo="Portaria" itens={portariaHoje} />
      </div>
      <p className="text-center text-[11px] text-slate-400">
        Experimente criar um aviso, um chamado ou uma reserva nas outras abas - esta visão
        atualiza sozinha.
      </p>
    </div>
  );
}

// ----- Transparência (só leitura, é um relatório na vida real também) -----
function AbaTransparencia() {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-3 gap-2">
        <Tile label="Pago" valor="R$ 18,4k" nota="Este mês" cor="text-emerald-600" />
        <Tile label="Pendente" valor="R$ 3,1k" nota="A vencer" cor="text-amber-600" />
        <Tile label="Total" valor="R$ 21,5k" nota="Previsto" cor="text-ink" />
      </div>
      <Lista
        titulo="Por categoria"
        itens={["Água - R$ 2.100", "Manutenção - R$ 4.800", "Zeladoria - R$ 5.200"]}
      />
      <div className="rounded-xl bg-slate-50 p-3">
        <p className="text-[11px] font-medium text-slate-500">Prévia da unidade (Bloco A - 101)</p>
        <div className="mt-2 grid grid-cols-3 gap-2 text-center">
          <div>
            <p className="text-[10px] text-slate-500">Rateio</p>
            <p className="text-sm font-semibold text-slate-700">R$ 412,00</p>
          </div>
          <div>
            <p className="text-[10px] text-slate-500">Multas</p>
            <p className="text-sm font-semibold text-red-700">R$ 0,00</p>
          </div>
          <div>
            <p className="text-[10px] text-slate-500">Total</p>
            <p className="text-sm font-semibold text-ink">R$ 412,00</p>
          </div>
        </div>
      </div>
    </div>
  );
}

interface Aviso {
  id: number;
  titulo: string;
  mensagem: string;
  tipo: "Condomínio" | "Ocorrência";
}

function AbaAvisos({
  avisos,
  onCriar,
}: {
  avisos: Aviso[];
  onCriar: (a: Omit<Aviso, "id">) => void;
}) {
  const [titulo, setTitulo] = useState("");
  const [mensagem, setMensagem] = useState("");
  const [tipo, setTipo] = useState<Aviso["tipo"]>("Condomínio");

  function onSubmit(event: FormEvent): void {
    event.preventDefault();
    if (!titulo.trim() || !mensagem.trim()) return;
    onCriar({ titulo, mensagem, tipo });
    setTitulo("");
    setMensagem("");
  }

  return (
    <div className="space-y-3">
      <form onSubmit={onSubmit} className="space-y-2 rounded-xl border border-dashed border-slate-300 p-3">
        <p className="text-[11px] font-medium text-slate-500">Publicar novo aviso / ocorrência</p>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-[1fr_auto]">
          <input
            value={titulo}
            onChange={(e) => setTitulo(e.target.value)}
            placeholder="Título"
            className={campoClasse}
          />
          <select value={tipo} onChange={(e) => setTipo(e.target.value as Aviso["tipo"])} className={campoClasse}>
            <option>Condomínio</option>
            <option>Ocorrência</option>
          </select>
        </div>
        <div className="flex gap-2">
          <input
            value={mensagem}
            onChange={(e) => setMensagem(e.target.value)}
            placeholder="Mensagem"
            className={campoClasse}
          />
          <button type="submit" className={botaoClasse}>
            Publicar
          </button>
        </div>
      </form>

      <div className="space-y-2">
        {avisos.map((aviso) => (
          <div key={aviso.id} className="rounded-xl bg-slate-50 p-3">
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm font-medium text-slate-800">{aviso.titulo}</p>
              <Badge
                texto={aviso.tipo}
                cor={aviso.tipo === "Condomínio" ? "bg-brand-100 text-brand-700" : "bg-amber-100 text-amber-700"}
              />
            </div>
            <p className="mt-1 text-xs text-slate-500">{aviso.mensagem}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

interface Chamado {
  id: number;
  titulo: string;
  status: "Aberto" | "Em andamento" | "Resolvido";
}

const PROXIMO_STATUS: Record<Chamado["status"], Chamado["status"]> = {
  Aberto: "Em andamento",
  "Em andamento": "Resolvido",
  Resolvido: "Resolvido",
};

const STATUS_COR: Record<Chamado["status"], string> = {
  Aberto: "bg-amber-100 text-amber-700",
  "Em andamento": "bg-brand-100 text-brand-700",
  Resolvido: "bg-emerald-100 text-emerald-700",
};

function AbaChamados({
  chamados,
  onCriar,
  onAvancar,
}: {
  chamados: Chamado[];
  onCriar: (titulo: string) => void;
  onAvancar: (id: number) => void;
}) {
  const [titulo, setTitulo] = useState("");

  function onSubmit(event: FormEvent): void {
    event.preventDefault();
    if (!titulo.trim()) return;
    onCriar(titulo);
    setTitulo("");
  }

  return (
    <div className="space-y-3">
      <form onSubmit={onSubmit} className="flex gap-2 rounded-xl border border-dashed border-slate-300 p-3">
        <input
          value={titulo}
          onChange={(e) => setTitulo(e.target.value)}
          placeholder="Descreva o chamado (ex.: Troca de lâmpada no hall)"
          className={campoClasse}
        />
        <button type="submit" className={botaoClasse}>
          Abrir
        </button>
      </form>

      <div className="space-y-2">
        {chamados.map((chamado) => (
          <div key={chamado.id} className="flex items-center justify-between rounded-xl bg-slate-50 p-3">
            <p className="text-sm text-slate-700">{chamado.titulo}</p>
            <div className="flex shrink-0 items-center gap-2">
              <Badge texto={chamado.status} cor={STATUS_COR[chamado.status]} />
              {chamado.status !== "Resolvido" && (
                <button
                  type="button"
                  onClick={() => onAvancar(chamado.id)}
                  className="text-[11px] font-medium text-brand-600"
                >
                  Avançar
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

interface Reuniao {
  id: number;
  titulo: string;
  data: string;
  local: string;
}

function AbaReunioes({ reunioes, onCriar }: { reunioes: Reuniao[]; onCriar: (r: Omit<Reuniao, "id">) => void }) {
  const [titulo, setTitulo] = useState("");
  const [data, setData] = useState("");
  const [local, setLocal] = useState("Salão de festas");

  function onSubmit(event: FormEvent): void {
    event.preventDefault();
    if (!titulo.trim() || !data) return;
    onCriar({ titulo, data, local });
    setTitulo("");
    setData("");
  }

  return (
    <div className="space-y-3">
      <form onSubmit={onSubmit} className="space-y-2 rounded-xl border border-dashed border-slate-300 p-3">
        <p className="text-[11px] font-medium text-slate-500">Convocar reunião</p>
        <input
          value={titulo}
          onChange={(e) => setTitulo(e.target.value)}
          placeholder="Título (ex.: Assembleia extraordinária)"
          className={campoClasse}
        />
        <div className="flex gap-2">
          <input type="date" value={data} onChange={(e) => setData(e.target.value)} className={campoClasse} />
          <input value={local} onChange={(e) => setLocal(e.target.value)} className={campoClasse} />
          <button type="submit" className={botaoClasse}>
            Convocar
          </button>
        </div>
      </form>

      <div className="space-y-2">
        {reunioes.map((reuniao) => (
          <div key={reuniao.id} className="rounded-xl bg-slate-50 p-3">
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm font-medium text-slate-800">{reuniao.titulo}</p>
              <Badge texto="Convocada" cor="bg-amber-100 text-amber-700" />
            </div>
            <p className="mt-1 text-xs text-slate-500">
              {reuniao.data ? new Date(`${reuniao.data}T00:00:00`).toLocaleDateString("pt-BR") : ""} -{" "}
              {reuniao.local}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

function AbaPortaria({
  visitantes,
  entregas,
  onCriarVisitante,
  onCriarEntrega,
}: {
  visitantes: string[];
  entregas: string[];
  onCriarVisitante: (v: string) => void;
  onCriarEntrega: (e: string) => void;
}) {
  const [nomeVisitante, setNomeVisitante] = useState("");
  const [unidadeVisitante, setUnidadeVisitante] = useState("");
  const [descricaoEntrega, setDescricaoEntrega] = useState("");

  function onSubmitVisitante(event: FormEvent): void {
    event.preventDefault();
    if (!nomeVisitante.trim() || !unidadeVisitante.trim()) return;
    onCriarVisitante(`${nomeVisitante} - ${unidadeVisitante}`);
    setNomeVisitante("");
    setUnidadeVisitante("");
  }

  function onSubmitEntrega(event: FormEvent): void {
    event.preventDefault();
    if (!descricaoEntrega.trim()) return;
    onCriarEntrega(descricaoEntrega);
    setDescricaoEntrega("");
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <div className="space-y-2">
        <form onSubmit={onSubmitVisitante} className="space-y-2 rounded-xl border border-dashed border-slate-300 p-3">
          <p className="text-[11px] font-medium text-slate-500">Registrar visitante</p>
          <input
            value={nomeVisitante}
            onChange={(e) => setNomeVisitante(e.target.value)}
            placeholder="Nome completo"
            className={campoClasse}
          />
          <div className="flex gap-2">
            <input
              value={unidadeVisitante}
              onChange={(e) => setUnidadeVisitante(e.target.value)}
              placeholder="Unidade (ex.: Bloco A, 101)"
              className={campoClasse}
            />
            <button type="submit" className={botaoClasse}>
              Registrar
            </button>
          </div>
        </form>
        <Lista titulo="Visitantes hoje" itens={visitantes} />
      </div>

      <div className="space-y-2">
        <form onSubmit={onSubmitEntrega} className="space-y-2 rounded-xl border border-dashed border-slate-300 p-3">
          <p className="text-[11px] font-medium text-slate-500">Registrar entrega</p>
          <div className="flex gap-2">
            <input
              value={descricaoEntrega}
              onChange={(e) => setDescricaoEntrega(e.target.value)}
              placeholder="Ex.: Pacote Amazon - Bloco A, 101"
              className={campoClasse}
            />
            <button type="submit" className={botaoClasse}>
              Registrar
            </button>
          </div>
        </form>
        <Lista titulo="Entregas" itens={entregas} />
      </div>
    </div>
  );
}

interface ReservaEspaco {
  id: number;
  area: string;
  data: string;
}

function AbaReservas({
  reservas,
  onCriar,
}: {
  reservas: ReservaEspaco[];
  onCriar: (r: Omit<ReservaEspaco, "id">) => { ok: boolean };
}) {
  const [area, setArea] = useState("Salão de festas");
  const [data, setData] = useState("");
  const [conflito, setConflito] = useState(false);

  function onSubmit(event: FormEvent): void {
    event.preventDefault();
    if (!data) return;
    const resultado = onCriar({ area, data });
    setConflito(!resultado.ok);
    if (resultado.ok) setData("");
  }

  return (
    <div className="space-y-3">
      <form onSubmit={onSubmit} className="space-y-2 rounded-xl border border-dashed border-slate-300 p-3">
        <p className="text-[11px] font-medium text-slate-500">Reservar uma área</p>
        <div className="flex gap-2">
          <select value={area} onChange={(e) => setArea(e.target.value)} className={campoClasse}>
            <option>Salão de festas</option>
            <option>Churrasqueira</option>
            <option>Quadra poliesportiva</option>
          </select>
          <input type="date" value={data} onChange={(e) => setData(e.target.value)} className={campoClasse} />
          <button type="submit" className={botaoClasse}>
            Reservar
          </button>
        </div>
        {conflito && (
          <p className="text-xs text-red-600">Esta área já está reservada nessa data - escolha outra.</p>
        )}
      </form>

      <div className="space-y-2">
        {reservas.map((reserva) => (
          <div key={reserva.id} className="flex items-center justify-between rounded-xl bg-slate-50 p-3">
            <div>
              <p className="text-sm font-medium text-slate-800">{reserva.area}</p>
              <p className="text-xs text-slate-500">
                {new Date(`${reserva.data}T00:00:00`).toLocaleDateString("pt-BR")}
              </p>
            </div>
            <Badge texto="Confirmada" cor="bg-emerald-100 text-emerald-700" />
          </div>
        ))}
      </div>
    </div>
  );
}

interface NotificacaoDemo {
  id: number;
  titulo: string;
  msg: string;
  lida: boolean;
}

function AbaNotificacoes({
  notificacoes,
  onMarcarTodasLidas,
}: {
  notificacoes: NotificacaoDemo[];
  onMarcarTodasLidas: () => void;
}) {
  const naoLidas = notificacoes.filter((n) => !n.lida).length;
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-500">{naoLidas} não lida(s)</p>
        {naoLidas > 0 && (
          <button type="button" onClick={onMarcarTodasLidas} className="text-xs font-medium text-brand-600">
            Marcar todas como lidas
          </button>
        )}
      </div>
      {notificacoes.length === 0 && (
        <p className="rounded-xl bg-slate-50 p-4 text-center text-sm text-slate-400">
          Crie algo nas outras abas para ver uma notificação aparecer aqui.
        </p>
      )}
      {notificacoes.map((n) => (
        <div key={n.id} className={`rounded-lg p-2.5 ${n.lida ? "bg-slate-50" : "bg-brand-50/60"}`}>
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm font-medium text-slate-800">{n.titulo}</p>
            {!n.lida && <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-brand-600" />}
          </div>
          <p className="text-xs text-slate-500">{n.msg}</p>
        </div>
      ))}
    </div>
  );
}

export function DemoTour({ onClose }: { onClose: () => void }) {
  const [abaAtiva, setAbaAtiva] = useState(0);

  const [avisos, setAvisos] = useState<Aviso[]>([
    { id: novoId(), titulo: "Manutenção do elevador", mensagem: "Amanhã, das 9h às 12h - bloco B fora de operação.", tipo: "Condomínio" },
    { id: novoId(), titulo: "Vazamento na garagem", mensagem: "Registrado por um morador - visível à gestão.", tipo: "Ocorrência" },
  ]);
  const [chamados, setChamados] = useState<Chamado[]>([
    { id: novoId(), titulo: "Troca de lâmpada - hall 2º andar", status: "Aberto" },
    { id: novoId(), titulo: "Vazamento na piscina", status: "Em andamento" },
  ]);
  const [reunioes, setReunioes] = useState<Reuniao[]>([
    { id: novoId(), titulo: "Assembleia ordinária", data: "2026-12-12", local: "Salão de festas" },
  ]);
  const [visitantes, setVisitantes] = useState<string[]>(["João da Silva - Bloco A, 101"]);
  const [entregas, setEntregas] = useState<string[]>(["Pacote Amazon - Bloco A, 101"]);
  const [reservas, setReservas] = useState<ReservaEspaco[]>([
    { id: novoId(), area: "Salão de festas", data: "2026-11-18" },
  ]);
  const [notificacoes, setNotificacoes] = useState<NotificacaoDemo[]>([
    { id: novoId(), titulo: "Reunião convocada", msg: "Assembleia ordinária - 12/12", lida: false },
  ]);

  function notificar(titulo: string, msg: string): void {
    setNotificacoes((prev) => [{ id: novoId(), titulo, msg, lida: false }, ...prev]);
  }

  const chamadosAbertos = chamados.filter((c) => c.status !== "Resolvido").length;

  const ABAS = [
    {
      titulo: "Dashboard",
      conteudo: (
        <AbaDashboard
          chamadosAbertos={chamadosAbertos}
          totalReservas={reservas.length}
          avisosRecentes={avisos.slice(0, 2).map((a) => a.titulo)}
          portariaHoje={[...visitantes.slice(0, 1), ...entregas.slice(0, 1)]}
        />
      ),
    },
    { titulo: "Transparência", conteudo: <AbaTransparencia /> },
    {
      titulo: "Avisos e Ocorrências",
      conteudo: (
        <AbaAvisos
          avisos={avisos}
          onCriar={(a) => {
            setAvisos((prev) => [{ ...a, id: novoId() }, ...prev]);
            notificar(a.titulo, a.tipo === "Condomínio" ? "Novo aviso do condomínio" : "Nova ocorrência registrada");
          }}
        />
      ),
    },
    {
      titulo: "Chamados",
      conteudo: (
        <AbaChamados
          chamados={chamados}
          onCriar={(titulo) => {
            setChamados((prev) => [{ id: novoId(), titulo, status: "Aberto" }, ...prev]);
            notificar("Chamado aberto", titulo);
          }}
          onAvancar={(id) =>
            setChamados((prev) =>
              prev.map((c) => (c.id === id ? { ...c, status: PROXIMO_STATUS[c.status] } : c))
            )
          }
        />
      ),
    },
    {
      titulo: "Reuniões",
      conteudo: (
        <AbaReunioes
          reunioes={reunioes}
          onCriar={(r) => {
            setReunioes((prev) => [{ ...r, id: novoId() }, ...prev]);
            notificar("Reunião convocada", r.titulo);
          }}
        />
      ),
    },
    {
      titulo: "Portaria",
      conteudo: (
        <AbaPortaria
          visitantes={visitantes}
          entregas={entregas}
          onCriarVisitante={(v) => {
            setVisitantes((prev) => [v, ...prev]);
            notificar("Novo visitante", v);
          }}
          onCriarEntrega={(e) => {
            setEntregas((prev) => [e, ...prev]);
            notificar("Nova entrega", e);
          }}
        />
      ),
    },
    {
      titulo: "Reserva de Espaços",
      conteudo: (
        <AbaReservas
          reservas={reservas}
          onCriar={(r) => {
            const jaReservado = reservas.some((x) => x.area === r.area && x.data === r.data);
            if (jaReservado) return { ok: false };
            setReservas((prev) => [{ ...r, id: novoId() }, ...prev]);
            notificar("Reserva confirmada", `${r.area} - ${new Date(`${r.data}T00:00:00`).toLocaleDateString("pt-BR")}`);
            return { ok: true };
          }}
        />
      ),
    },
    {
      titulo: "Notificações",
      conteudo: (
        <AbaNotificacoes
          notificacoes={notificacoes}
          onMarcarTodasLidas={() => setNotificacoes((prev) => prev.map((n) => ({ ...n, lida: true })))}
        />
      ),
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-ink/60 p-3 sm:items-center sm:justify-center sm:p-6">
      <div className="absolute inset-0" onClick={onClose} aria-hidden="true" />
      <div className="relative flex w-full max-w-3xl flex-1 flex-col overflow-hidden rounded-2xl bg-white shadow-2xl sm:flex-none">
        <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
          <div className="flex items-center gap-2">
            <img src={logoIcon} alt="" className="h-7 w-auto" />
            <div>
              <p className="text-sm font-bold text-ink">Prévia do Meu Prédio</p>
              <p className="text-[11px] text-slate-400">
                Demonstração interativa - crie o que quiser, nada é salvo de verdade
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Fechar"
            className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100"
          >
            <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5">
              <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        <div className="flex gap-1 overflow-x-auto border-b border-slate-100 px-3 py-2 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {ABAS.map((aba, indice) => (
            <button
              key={aba.titulo}
              type="button"
              onClick={() => setAbaAtiva(indice)}
              className={`relative shrink-0 rounded-lg px-3 py-1.5 text-xs font-medium ${
                indice === abaAtiva ? "bg-brand-600 text-white" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {aba.titulo}
              {aba.titulo === "Notificações" && notificacoes.some((n) => !n.lida) && (
                <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-red-500" />
              )}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto bg-slate-50/50 p-4">{ABAS[abaAtiva].conteudo}</div>

        <div className="border-t border-slate-100 px-4 py-3 text-center">
          <p className="text-xs text-slate-500">Gostou do que viu? Fale com a gente ou entre no sistema.</p>
        </div>
      </div>
    </div>
  );
}
