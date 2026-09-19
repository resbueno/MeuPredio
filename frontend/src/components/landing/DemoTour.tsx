import { useState } from "react";
import logoIcon from "../../assets/logo-icon.png";

interface Aba {
  titulo: string;
  conteudo: JSX.Element;
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
        {itens.map((item) => (
          <li key={item}>• {item}</li>
        ))}
      </ul>
    </div>
  );
}

function Badge({ texto, cor }: { texto: string; cor: string }) {
  return <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${cor}`}>{texto}</span>;
}

const ABAS: Aba[] = [
  {
    titulo: "Dashboard",
    conteudo: (
      <div className="space-y-3">
        <div className="grid grid-cols-3 gap-2">
          <Tile label="Moradores" valor="128" nota="Vinculados" cor="text-emerald-600" />
          <Tile label="Manutenções" valor="06" nota="Em andamento" cor="text-amber-600" />
          <Tile label="Reservas" valor="05" nota="Este mês" cor="text-brand-600" />
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
          <Lista titulo="Avisos recentes" itens={["Limpeza da garagem", "Reunião confirmada"]} />
          <Lista titulo="Portaria" itens={["2 visitantes hoje", "1 encomenda recebida"]} />
        </div>
      </div>
    ),
  },
  {
    titulo: "Transparência",
    conteudo: (
      <div className="space-y-3">
        <div className="grid grid-cols-3 gap-2">
          <Tile label="Pago" valor="R$ 18.4k" nota="Este mês" cor="text-emerald-600" />
          <Tile label="Pendente" valor="R$ 3.1k" nota="A vencer" cor="text-amber-600" />
          <Tile label="Total" valor="R$ 21.5k" nota="Previsto" cor="text-ink" />
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
    ),
  },
  {
    titulo: "Avisos e Ocorrências",
    conteudo: (
      <div className="space-y-2">
        <div className="rounded-xl bg-slate-50 p-3">
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm font-medium text-slate-800">Manutenção do elevador</p>
            <Badge texto="Condomínio" cor="bg-brand-100 text-brand-700" />
          </div>
          <p className="mt-1 text-xs text-slate-500">Amanhã, das 9h às 12h - bloco B fora de operação.</p>
        </div>
        <div className="rounded-xl bg-slate-50 p-3">
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm font-medium text-slate-800">Vazamento na garagem</p>
            <Badge texto="Ocorrência" cor="bg-amber-100 text-amber-700" />
          </div>
          <p className="mt-1 text-xs text-slate-500">Registrado por um morador - visível à gestão.</p>
        </div>
        <div className="rounded-xl bg-slate-50 p-3">
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm font-medium text-slate-800">Barulho após 22h</p>
            <Badge texto="Aviso direto" cor="bg-slate-200 text-slate-600" />
          </div>
          <p className="mt-1 text-xs text-slate-500">Enviado só para a unidade 304.</p>
        </div>
      </div>
    ),
  },
  {
    titulo: "Chamados",
    conteudo: (
      <div className="space-y-2">
        {[
          { titulo: "Troca de lâmpada - hall 2º andar", status: "Aberto", cor: "bg-amber-100 text-amber-700" },
          { titulo: "Vazamento na piscina", status: "Em andamento", cor: "bg-brand-100 text-brand-700" },
          { titulo: "Portão da garagem com ruído", status: "Resolvido", cor: "bg-emerald-100 text-emerald-700" },
        ].map((chamado) => (
          <div key={chamado.titulo} className="flex items-center justify-between rounded-xl bg-slate-50 p-3">
            <p className="text-sm text-slate-700">{chamado.titulo}</p>
            <Badge texto={chamado.status} cor={chamado.cor} />
          </div>
        ))}
      </div>
    ),
  },
  {
    titulo: "Reuniões",
    conteudo: (
      <div className="space-y-2">
        <div className="rounded-xl bg-slate-50 p-3">
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm font-medium text-slate-800">Assembleia ordinária</p>
            <Badge texto="Ordinária" cor="bg-amber-100 text-amber-700" />
          </div>
          <p className="mt-1 text-sm capitalize text-slate-600">Quinta-feira, 12/12 às 19h</p>
          <p className="text-xs text-slate-500">Salão de festas</p>
          <p className="mt-2 border-t border-slate-200 pt-2 text-xs text-slate-500">
            18 de 40 unidades confirmaram presença
          </p>
        </div>
        <div className="rounded-xl bg-slate-50 p-3">
          <p className="text-[11px] font-medium text-slate-500">Ata registrada</p>
          <p className="mt-1 text-xs text-slate-600">"Reforma do playground - aprovada por unanimidade."</p>
        </div>
      </div>
    ),
  },
  {
    titulo: "Portaria",
    conteudo: (
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="rounded-xl bg-slate-50 p-3">
          <p className="mb-2 text-[11px] font-medium text-slate-500">Visitantes hoje</p>
          <div className="space-y-2 text-xs text-slate-600">
            <p>• João da Silva (RG) - Bloco A, 101 - 🚗 Onix prata</p>
            <p>• Maria Souza (não informado) - Bloco B, 202</p>
          </div>
        </div>
        <div className="rounded-xl bg-slate-50 p-3">
          <p className="mb-2 text-[11px] font-medium text-slate-500">Entregas</p>
          <div className="space-y-2 text-xs text-slate-600">
            <p>• Pacote Amazon - Bloco A, 101 - aguardando retirada</p>
            <p>• Caixa dos Correios - Bloco C, 304 - retirada</p>
          </div>
        </div>
      </div>
    ),
  },
  {
    titulo: "Reserva de Espaços",
    conteudo: (
      <div className="space-y-2">
        <div className="rounded-xl bg-slate-50 p-3">
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm font-medium text-slate-800">Salão de festas</p>
            <Badge texto="Ativa" cor="bg-emerald-100 text-emerald-700" />
          </div>
          <p className="mt-1 text-xs text-slate-500">Agenda liberada até 18/11 - capacidade 50 pessoas</p>
        </div>
        <div className="rounded-xl bg-slate-50 p-3">
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm font-medium text-slate-800">Churrasqueira</p>
            <Badge texto="Confirmada" cor="bg-emerald-100 text-emerald-700" />
          </div>
          <p className="mt-1 text-xs text-slate-500">Reservada por Bloco A, 101 - sábado, 23/11</p>
        </div>
      </div>
    ),
  },
  {
    titulo: "Notificações",
    conteudo: (
      <div className="space-y-1">
        {[
          { titulo: "Reunião convocada", msg: "Assembleia ordinária - 12/12 às 19h", lida: false },
          { titulo: "Nova entrega", msg: "Pacote Amazon - Portaria", lida: false },
          { titulo: "Aviso do condomínio", msg: "Manutenção do elevador amanhã", lida: true },
        ].map((n) => (
          <div key={n.titulo} className={`rounded-lg p-2.5 ${n.lida ? "" : "bg-brand-50/60"}`}>
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm font-medium text-slate-800">{n.titulo}</p>
              {!n.lida && <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-brand-600" />}
            </div>
            <p className="text-xs text-slate-500">{n.msg}</p>
          </div>
        ))}
      </div>
    ),
  },
];

export function DemoTour({ onClose }: { onClose: () => void }) {
  const [abaAtiva, setAbaAtiva] = useState(0);

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-ink/60 p-3 sm:items-center sm:justify-center sm:p-6">
      <div
        className="absolute inset-0"
        onClick={onClose}
        aria-hidden="true"
      />
      <div className="relative flex w-full max-w-3xl flex-1 flex-col overflow-hidden rounded-2xl bg-white shadow-2xl sm:flex-none">
        <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
          <div className="flex items-center gap-2">
            <img src={logoIcon} alt="" className="h-7 w-auto" />
            <div>
              <p className="text-sm font-bold text-ink">Prévia do Meu Prédio</p>
              <p className="text-[11px] text-slate-400">Demonstração com dados fictícios - nada é salvo</p>
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
              className={`shrink-0 rounded-lg px-3 py-1.5 text-xs font-medium ${
                indice === abaAtiva ? "bg-brand-600 text-white" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {aba.titulo}
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
