import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  contarNotificacoesNaoLidas,
  listNotificacoes,
  marcarNotificacaoLida,
  marcarTodasNotificacoesLidas,
} from "../../api/notificacoes";
import type { Notificacao } from "../../api/types";

const ROTA_POR_REFERENCIA: Record<string, string> = {
  aviso_mural: "/avisos",
  aviso_direto: "/avisos-diretos",
  ocorrencia: "/ocorrencias",
  reuniao: "/reunioes",
  entrega: "/entregas",
};

function formatarRelativo(dataIso: string): string {
  const diffMs = Date.now() - new Date(dataIso).getTime();
  const minutos = Math.floor(diffMs / 60000);
  if (minutos < 1) return "agora";
  if (minutos < 60) return `${minutos} min atrás`;
  const horas = Math.floor(minutos / 60);
  if (horas < 24) return `${horas}h atrás`;
  const dias = Math.floor(horas / 24);
  return `${dias}d atrás`;
}

export function NotificacaoBell({ userId }: { userId: number }) {
  const [aberto, setAberto] = useState(false);
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const { data: contagem } = useQuery({
    queryKey: ["notificacoes", "contagem", userId],
    queryFn: contarNotificacoesNaoLidas,
    refetchInterval: 60_000,
  });

  const { data: notificacoes, isLoading } = useQuery({
    queryKey: ["notificacoes", "lista", userId],
    queryFn: () => listNotificacoes(),
    enabled: aberto,
  });

  function invalidar(): void {
    queryClient.invalidateQueries({ queryKey: ["notificacoes"] });
  }

  function abrirNotificacao(notificacao: Notificacao): void {
    if (!notificacao.lida_em) {
      marcarNotificacaoLida(notificacao.id).then(invalidar);
    }
    setAberto(false);
    if (notificacao.referencia_tipo && ROTA_POR_REFERENCIA[notificacao.referencia_tipo]) {
      navigate(ROTA_POR_REFERENCIA[notificacao.referencia_tipo]);
    }
  }

  const naoLidas = contagem?.nao_lidas ?? 0;

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setAberto((v) => !v)}
        aria-label="Notificações"
        className="relative rounded-lg p-1.5 text-slate-600 hover:bg-slate-100"
      >
        <svg viewBox="0 0 24 24" fill="none" className="h-6 w-6">
          <path
            d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M13.73 21a2 2 0 01-3.46 0"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        {naoLidas > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-semibold text-white">
            {naoLidas > 99 ? "99+" : naoLidas}
          </span>
        )}
      </button>

      {aberto && (
        <>
          <div className="fixed inset-0 z-30" onClick={() => setAberto(false)} aria-hidden="true" />
          <div className="absolute right-0 top-full z-40 mt-2 max-h-[70vh] w-80 max-w-[90vw] overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-100 px-3 py-2">
              <p className="text-sm font-semibold text-slate-700">Notificações</p>
              {naoLidas > 0 && (
                <button
                  type="button"
                  onClick={() => marcarTodasNotificacoesLidas().then(invalidar)}
                  className="text-xs font-medium text-brand-600"
                >
                  Marcar todas como lidas
                </button>
              )}
            </div>
            {isLoading && <p className="p-3 text-sm text-slate-500">Carregando...</p>}
            <ul className="divide-y divide-slate-100">
              {notificacoes?.map((notificacao) => (
                <li key={notificacao.id}>
                  <button
                    type="button"
                    onClick={() => abrirNotificacao(notificacao)}
                    className={`block w-full px-3 py-2.5 text-left hover:bg-slate-50 ${
                      notificacao.lida_em ? "" : "bg-brand-50/60"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-medium text-slate-800">{notificacao.titulo}</p>
                      {!notificacao.lida_em && (
                        <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-brand-600" />
                      )}
                    </div>
                    <p className="mt-0.5 line-clamp-2 text-xs text-slate-500">{notificacao.mensagem}</p>
                    <p className="mt-1 text-[11px] text-slate-400">
                      {formatarRelativo(notificacao.created_at)}
                    </p>
                  </button>
                </li>
              ))}
              {notificacoes?.length === 0 && (
                <li className="p-4 text-center text-sm text-slate-500">Nenhuma notificação.</li>
              )}
            </ul>
          </div>
        </>
      )}
    </div>
  );
}
