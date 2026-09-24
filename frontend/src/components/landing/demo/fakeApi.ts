/**
 * "Backend" falso, em memória, usado só pela prévia interativa da landing
 * page. As páginas reais do app rodam por cima dele via um adapter do axios
 * (ver DemoTour.tsx) - por isso o visual e o comportamento são exatamente
 * os do sistema, e nada é enviado nem gravado em servidor algum. Criado do
 * zero a cada abertura da prévia; fechar descarta tudo.
 */
import { AxiosError, type AxiosAdapter, type AxiosResponse, type InternalAxiosRequestConfig } from "axios";
import type {
  AreaComum,
  AvisoDireto,
  AvisoMural,
  DespesaLancamento,
  DespesaRecorrente,
  Entrega,
  Fornecedor,
  ModuloEnum,
  Notificacao,
  Ocorrencia,
  Reserva,
  Reuniao,
  TicketAtendimento,
  Unidade,
  Usuario,
  Visitante,
} from "../../../api/types";
import { TODOS_MODULOS } from "../../../api/types";

const MODULOS_DEMO: ModuloEnum[] = TODOS_MODULOS.map((m) => m.value);

type Json = Record<string, unknown>;
type Resultado = { status?: number; data?: unknown };

const PREDIO_ID = 1;
export const USUARIO_DEMO_ID = 1;

function iso(dias = 0, horas = 0): string {
  return new Date(Date.now() + dias * 86_400_000 + horas * 3_600_000).toISOString();
}
function dia(dias = 0): string {
  return iso(dias).slice(0, 10);
}
function erro(status: number, detail: string): never {
  throw { __demoErro: true, status, detail };
}

export function usuarioDemo(): Usuario {
  return {
    id: USUARIO_DEMO_ID,
    email: "sindico@exemplo.com.br",
    full_name: "Carlos Almeida",
    role: "sindico",
    predio_id: PREDIO_ID,
    unidade_ids: [1],
    papeis_extra: ["morador"],
    is_active: true,
    consent_lgpd_accepted_at: iso(-30),
    last_login_at: iso(0, -1),
    created_at: iso(-200),
    updated_at: iso(-1),
    deleted_at: null,
    anonymized_at: null,
    modulos_habilitados: MODULOS_DEMO,
  };
}

export function criarBackendFalso() {
  let seq = 100;
  const nid = () => ++seq;

  const unidades: Unidade[] = [
    ["A", "101", "12"], ["A", "102", "13"], ["A", "201", "14"],
    ["A", "202", "15"], ["B", "101", "22"], ["B", "102", "23"],
  ].map(([bloco, numero, vaga], i) => ({
    id: i + 1, predio_id: PREDIO_ID, bloco, numero, vaga,
    created_at: iso(-200), updated_at: iso(-200), deleted_at: null,
  }));

  const usuarios: Usuario[] = [
    usuarioDemo(),
    { ...usuarioDemo(), id: 2, full_name: "Marina Souza", email: "marina@exemplo.com.br", role: "morador", papeis_extra: [], unidade_ids: [2], last_login_at: iso(0, -2) },
    { ...usuarioDemo(), id: 3, full_name: "Paulo Ribeiro", email: "paulo@exemplo.com.br", role: "proprietario", papeis_extra: [], unidade_ids: [3], last_login_at: iso(-3) },
    { ...usuarioDemo(), id: 4, full_name: "Joana Lima", email: "joana@exemplo.com.br", role: "morador", papeis_extra: [], unidade_ids: [5], last_login_at: iso(-1) },
    { ...usuarioDemo(), id: 5, full_name: "Sr. Antônio", email: "zelador@exemplo.com.br", role: "zelador", papeis_extra: [], unidade_ids: [], last_login_at: iso(0, -5) },
  ];

  const avisosMural: AvisoMural[] = [
    { id: 1, predio_id: PREDIO_ID, tipo: "condominio", titulo: "Manutenção do elevador", descricao: "Amanhã, das 9h às 12h, o elevador do bloco B ficará fora de operação.", preco: null, created_by: 1, created_at: iso(-1), updated_at: iso(-1) },
    { id: 2, predio_id: PREDIO_ID, tipo: "condominio", titulo: "Limpeza da caixa d'água", descricao: "No sábado haverá interrupção do fornecimento entre 8h e 14h.", preco: null, created_by: 1, created_at: iso(-4), updated_at: iso(-4) },
    { id: 3, predio_id: PREDIO_ID, tipo: "anuncio", titulo: "Vendo bicicleta aro 29", descricao: "Semi-nova, pouco uso. Falar com o apto 102.", preco: "850.00", created_by: 2, created_at: iso(-2), updated_at: iso(-2) },
  ];

  const avisosDiretos: AvisoDireto[] = [
    { id: 1, predio_id: PREDIO_ID, unidade_id: 2, destinatario: "ambos", tipo: "aviso", titulo: "Barulho após as 22h", mensagem: "Recebemos reclamações de barulho no período noturno. Pedimos atenção ao horário de silêncio.", valor: null, despesa_lancamento_id: null, lida_em: iso(-1), resposta: null, respondido_por: null, respondido_em: null, created_by: 1, created_at: iso(-2), updated_at: iso(-1) },
  ];

  const ocorrencias: Ocorrencia[] = [
    { id: 1, predio_id: PREDIO_ID, unidade_id: 2, titulo: "Vazamento na garagem", descricao: "Água acumulando perto da vaga 15, provavelmente de um cano do teto.", editado_em: null, editado_por: null, created_by: 2, created_at: iso(-1), updated_at: iso(-1) },
    { id: 2, predio_id: PREDIO_ID, unidade_id: null, titulo: "Portão social com ruído", descricao: "O portão da entrada principal está fazendo barulho ao abrir.", editado_em: null, editado_por: null, created_by: 3, created_at: iso(-5), updated_at: iso(-5) },
  ];

  const tickets: TicketAtendimento[] = [
    { id: 1, predio_id: PREDIO_ID, unidade_id: 2, responsavel_id: null, created_by: 2, titulo: "Troca de lâmpada no hall do 2º andar", descricao: "A lâmpada do hall queimou há dois dias.", categoria: "manutencao", prioridade: "media", status: "aberto", prazo_sla: iso(2), resolvido_em: null, esta_atrasado: false, comentarios: [], created_at: iso(-1), updated_at: iso(-1) },
    { id: 2, predio_id: PREDIO_ID, unidade_id: 3, responsavel_id: 5, created_by: 3, titulo: "Vazamento na piscina", descricao: "Nível da água caindo mais rápido que o normal.", categoria: "manutencao", prioridade: "alta", status: "em_andamento", prazo_sla: iso(1), resolvido_em: null, esta_atrasado: false, comentarios: [{ id: 1, ticket_id: 2, created_by: 5, mensagem: "Registro fechado, aguardando o encanador.", created_at: iso(0, -3) }], created_at: iso(-2), updated_at: iso(0, -3) },
    { id: 3, predio_id: PREDIO_ID, unidade_id: 5, responsavel_id: 5, created_by: 4, titulo: "Portão da garagem com ruído", descricao: "Barulho ao abrir e fechar.", categoria: "manutencao", prioridade: "baixa", status: "resolvido", prazo_sla: iso(-3), resolvido_em: iso(-4), esta_atrasado: false, comentarios: [], created_at: iso(-8), updated_at: iso(-4) },
  ];

  const reunioes: Reuniao[] = [
    { id: 1, predio_id: PREDIO_ID, tipo: "ordinaria", status: "convocada", titulo: "Assembleia geral ordinária", data_hora: iso(12), local: "Salão de festas", pauta: "1. Prestação de contas\n2. Previsão orçamentária\n3. Eleição de conselho", ata: null, ata_registrada_em: null, ata_registrada_por: null, created_by: 1, presencas: [{ id: 1, reuniao_id: 1, unidade_id: 2, created_by: 2, created_at: iso(-1) }], created_at: iso(-3), updated_at: iso(-3) },
    { id: 2, predio_id: PREDIO_ID, tipo: "extraordinaria", status: "realizada", titulo: "Reforma do playground", data_hora: iso(-30), local: "Salão de festas", pauta: "Aprovação do orçamento da reforma.", ata: "Orçamento aprovado por unanimidade. Obra prevista para o próximo trimestre.", ata_registrada_em: iso(-30), ata_registrada_por: 1, created_by: 1, presencas: [], created_at: iso(-40), updated_at: iso(-30) },
  ];

  const entregas: Entrega[] = [
    { id: 1, predio_id: PREDIO_ID, unidade_id: 1, descricao: "Pacote Amazon", localizacao: "Portaria, prateleira 2", retirada_em: null, retirada_por: null, created_by: 5, created_at: iso(0, -4), updated_at: iso(0, -4) },
    { id: 2, predio_id: PREDIO_ID, unidade_id: 3, descricao: "Caixa dos Correios", localizacao: "Portaria, prateleira 1", retirada_em: iso(-1), retirada_por: 3, created_by: 5, created_at: iso(-2), updated_at: iso(-1) },
  ];

  const visitantes: Visitante[] = [
    { id: 1, predio_id: PREDIO_ID, unidade_id: 2, nome_completo: "João da Silva", tipo_documento: "rg", numero_documento: "12.345.678-9", veiculo_placa: "ABC1D23", veiculo_modelo: "Onix", veiculo_cor: "Prata", created_by: 5, created_at: iso(0, -3) },
    { id: 2, predio_id: PREDIO_ID, unidade_id: 5, nome_completo: "Maria Souza", tipo_documento: "nao_informado", numero_documento: null, veiculo_placa: null, veiculo_modelo: null, veiculo_cor: null, created_by: 5, created_at: iso(0, -6) },
  ];

  const areas: AreaComum[] = [
    { id: 1, predio_id: PREDIO_ID, nome: "Salão de festas", descricao: "Capacidade para 50 pessoas, com cozinha.", capacidade: 50, ativo: true, agenda_liberada_ate: dia(60), created_at: iso(-100), updated_at: iso(-10) },
    { id: 2, predio_id: PREDIO_ID, nome: "Churrasqueira", descricao: null, capacidade: 20, ativo: true, agenda_liberada_ate: dia(30), created_at: iso(-100), updated_at: iso(-10) },
  ];

  const reservas: Reserva[] = [
    { id: 1, predio_id: PREDIO_ID, area_comum_id: 1, unidade_id: 2, data: dia(9), status: "confirmada", observacoes: "Aniversário de 8 anos", cancelada_em: null, cancelada_por: null, created_by: 2, created_at: iso(-2) },
  ];

  const fornecedores: Fornecedor[] = [];
  const recorrentes: DespesaRecorrente[] = [
    { id: 1, predio_id: PREDIO_ID, fornecedor_id: null, unidade_id: null, descricao: "Conta de água", categoria: "agua", valor: "2100.00", dia_vencimento: 10, ativo: true, data_inicio: dia(-120), data_fim: null, ultima_geracao: dia(-20), observacoes: null, created_at: iso(-120), updated_at: iso(-20) },
  ];

  const despesas: DespesaLancamento[] = [];
  const nUnidades = unidades.length;
  const semRateio = (id: number, descricao: string, categoria: string, valor: string, venc: string, status: DespesaLancamento["status"]): DespesaLancamento => ({
    id, predio_id: PREDIO_ID, unidade_id: null, fornecedor_id: null, descricao, categoria, valor,
    data_vencimento: venc, data_pagamento: status === "pago" ? venc : null, status, esta_atrasada: false,
    documento_url: null, comprovante_pagamento_url: null, observacoes: null, rateado_em: null, itens_rateio: [],
    created_at: iso(-40), updated_at: iso(-40), deleted_at: null,
  });
  const seedDesp: [string, string, string, number, DespesaLancamento["status"]][] = [
    ["Conta de água", "agua", "2100.00", -150, "pago"], ["Conta de luz - áreas comuns", "luz", "1350.00", -145, "pago"],
    ["Zeladoria", "condominio", "5200.00", -120, "pago"], ["Conta de água", "agua", "2050.00", -90, "pago"],
    ["Manutenção do elevador", "manutencao", "4800.00", -85, "pago"], ["Zeladoria", "condominio", "5200.00", -60, "pago"],
    ["Conta de água", "agua", "2200.00", -30, "pago"], ["Conta de luz - áreas comuns", "luz", "1420.00", -28, "pago"],
    ["Zeladoria", "condominio", "5200.00", -3, "pago"], ["Conta de água", "agua", "2100.00", 6, "pendente"],
    ["Manutenção da bomba", "manutencao", "980.00", 9, "pendente"],
  ];
  seedDesp.forEach(([d, c, v, off, st], i) => despesas.push(semRateio(i + 1, d, c, v, dia(off), st)));

  function ratear(d: DespesaLancamento, criterio: "igual" | "fracao_ideal") {
    const cada = (Number(d.valor) / nUnidades).toFixed(2);
    d.rateado_em = iso();
    d.itens_rateio = unidades.map((u) => ({ id: nid(), despesa_lancamento_id: d.id, unidade_id: u.id, valor: cada, criterio, created_at: iso() }));
  }
  despesas.filter((d) => d.status === "pago").forEach((d) => ratear(d, "igual"));

  const notificacoes: Notificacao[] = [
    { id: 1, tipo: "ocorrencia", titulo: "Nova ocorrência: Vazamento na garagem", mensagem: "Água acumulando perto da vaga 15, provavelmente de um cano do teto.", referencia_tipo: "ocorrencia", referencia_id: 1, lida_em: null, created_at: iso(0, -20) },
    { id: 2, tipo: "reuniao", titulo: "Reunião convocada: Assembleia geral ordinária", mensagem: "Salão de festas", referencia_tipo: "reuniao", referencia_id: 1, lida_em: null, created_at: iso(-3) },
    { id: 3, tipo: "aviso_geral", titulo: "Manutenção do elevador", mensagem: "Amanhã, das 9h às 12h, o elevador do bloco B ficará fora de operação.", referencia_tipo: "aviso_mural", referencia_id: 1, lida_em: iso(-1), created_at: iso(-1) },
  ];

  const ordenar = <T extends { created_at: string }>(l: T[]) => [...l].sort((a, b) => b.created_at.localeCompare(a.created_at));
  const id = (p: string) => Number(p);
  const achar = <T extends { id: number }>(l: T[], i: number, nome: string): T => l.find((x) => x.id === i) ?? erro(404, `${nome} não encontrado(a).`);
  const slaHoras = { alta: 24, media: 72, baixa: 168 } as const;

  function balancete(ano?: number, mes?: number) {
    const lista = despesas.filter((d) => {
      if (d.unidade_id != null) return false;
      const dt = new Date(`${d.data_vencimento}T00:00:00`);
      return (!ano || dt.getFullYear() === ano) && (!mes || dt.getMonth() + 1 === mes);
    });
    const soma = (f: (d: DespesaLancamento) => boolean) => lista.filter(f).reduce((s, d) => s + Number(d.valor), 0);
    const cats: Record<string, number> = {};
    lista.filter((d) => d.status !== "cancelado").forEach((d) => { cats[d.categoria] = (cats[d.categoria] ?? 0) + Number(d.valor); });
    return {
      ano: ano ?? new Date().getFullYear(), mes: mes ?? null,
      total_pago: soma((d) => d.status === "pago").toFixed(2),
      total_pendente: soma((d) => d.status === "pendente").toFixed(2),
      total_cancelado: soma((d) => d.status === "cancelado").toFixed(2),
      total_geral: soma((d) => d.status !== "cancelado").toFixed(2),
      por_categoria: Object.entries(cats).map(([categoria, total]) => ({ categoria, total: total.toFixed(2) })),
    };
  }

  function rota(metodo: string, url: string, p: Json, corpo: Json, form: FormData | null): Resultado {
    const seg = url.replace(/^\//, "").split("/");
    const [recurso, a, b] = seg;
    const q = (k: string) => (p[k] === undefined || p[k] === null ? undefined : String(p[k]));
    const hoje = dia();

    if (recurso === "usuarios") {
      if (b === "consentimento-lgpd") return { data: achar(usuarios, id(a), "Usuário") };
      if (metodo === "get" && a) return { data: achar(usuarios, id(a), "Usuário") };
      if (metodo === "get") return { data: usuarios };
    }
    if (recurso === "predios" && b === "integracao-ocr") return { data: { configurado: true }, status: metodo === "delete" ? 204 : 200 };
    if (recurso === "unidades") {
      if (metodo === "get") return { data: unidades };
      if (metodo === "post" && a === "lote") {
        const novos = (corpo.unidades as Json[]).map((u) => ({ id: nid(), predio_id: PREDIO_ID, bloco: String(u.bloco), numero: String(u.numero), vaga: (u.vaga as string) ?? null, created_at: iso(), updated_at: iso(), deleted_at: null }));
        unidades.push(...novos);
        return { status: 201, data: novos };
      }
      if (metodo === "post") {
        if (unidades.some((u) => u.bloco === corpo.bloco && u.numero === corpo.numero)) erro(409, "Já existe uma unidade com este bloco e número neste prédio.");
        const u: Unidade = { id: nid(), predio_id: PREDIO_ID, bloco: String(corpo.bloco), numero: String(corpo.numero), vaga: (corpo.vaga as string) ?? null, created_at: iso(), updated_at: iso(), deleted_at: null };
        unidades.push(u);
        return { status: 201, data: u };
      }
      if (metodo === "patch") return { data: Object.assign(achar(unidades, id(a), "Unidade"), corpo) };
      if (metodo === "delete") { unidades.splice(unidades.indexOf(achar(unidades, id(a), "Unidade")), 1); return { status: 204 }; }
    }
    if (recurso === "avisos-mural") {
      if (metodo === "get") return { data: ordenar(avisosMural).filter((x) => !q("tipo") || x.tipo === q("tipo")) };
      if (metodo === "post") {
        const n: AvisoMural = { id: nid(), predio_id: PREDIO_ID, tipo: corpo.tipo as AvisoMural["tipo"], titulo: String(corpo.titulo), descricao: String(corpo.descricao), preco: (corpo.preco as string) ?? null, created_by: USUARIO_DEMO_ID, created_at: iso(), updated_at: iso() };
        avisosMural.push(n);
        return { status: 201, data: n };
      }
      if (metodo === "patch") return { data: Object.assign(achar(avisosMural, id(a), "Aviso"), corpo, { updated_at: iso() }) };
      if (metodo === "delete") { avisosMural.splice(avisosMural.indexOf(achar(avisosMural, id(a), "Aviso")), 1); return { status: 204 }; }
    }
    if (recurso === "avisos-diretos") {
      if (metodo === "get") return { data: ordenar(avisosDiretos) };
      if (metodo === "post" && !a) {
        const tipo = corpo.tipo as AvisoDireto["tipo"];
        let despId: number | null = null;
        if (tipo === "multa") {
          despId = nid();
          despesas.push({ ...semRateio(despId, String(corpo.titulo), "multa", String(corpo.valor ?? "0"), String(corpo.data_vencimento ?? hoje), "pendente"), unidade_id: Number(corpo.unidade_id) });
        }
        const n: AvisoDireto = { id: nid(), predio_id: PREDIO_ID, unidade_id: Number(corpo.unidade_id), destinatario: corpo.destinatario as AvisoDireto["destinatario"], tipo, titulo: String(corpo.titulo), mensagem: String(corpo.mensagem), valor: (corpo.valor as string) ?? null, despesa_lancamento_id: despId, lida_em: null, resposta: null, respondido_por: null, respondido_em: null, created_by: USUARIO_DEMO_ID, created_at: iso(), updated_at: iso() };
        avisosDiretos.push(n);
        return { status: 201, data: n };
      }
      if (metodo === "post" && b === "marcar-lido") return { data: Object.assign(achar(avisosDiretos, id(a), "Aviso"), { lida_em: iso() }) };
      if (metodo === "post" && b === "responder") return { data: Object.assign(achar(avisosDiretos, id(a), "Aviso"), { resposta: corpo.resposta, respondido_por: USUARIO_DEMO_ID, respondido_em: iso(), lida_em: iso() }) };
      if (metodo === "delete") { avisosDiretos.splice(avisosDiretos.indexOf(achar(avisosDiretos, id(a), "Aviso")), 1); return { status: 204 }; }
    }
    if (recurso === "ocorrencias") {
      if (metodo === "get") return { data: ordenar(ocorrencias) };
      if (metodo === "post") {
        const n: Ocorrencia = { id: nid(), predio_id: PREDIO_ID, unidade_id: (corpo.unidade_id as number) ?? null, titulo: String(corpo.titulo), descricao: String(corpo.descricao), editado_em: null, editado_por: null, created_by: USUARIO_DEMO_ID, created_at: iso(), updated_at: iso() };
        ocorrencias.push(n);
        return { status: 201, data: n };
      }
      if (metodo === "patch") return { data: Object.assign(achar(ocorrencias, id(a), "Ocorrência"), corpo, { editado_em: iso(), editado_por: USUARIO_DEMO_ID }) };
    }
    if (recurso === "tickets") {
      if (metodo === "get") return { data: ordenar(tickets).filter((t) => !q("status") || t.status === q("status")) };
      if (metodo === "post" && !a) {
        const pr = corpo.prioridade as TicketAtendimento["prioridade"];
        const t: TicketAtendimento = { id: nid(), predio_id: PREDIO_ID, unidade_id: (corpo.unidade_id as number) ?? 1, responsavel_id: null, created_by: USUARIO_DEMO_ID, titulo: String(corpo.titulo), descricao: String(corpo.descricao), categoria: corpo.categoria as TicketAtendimento["categoria"], prioridade: pr, status: "aberto", prazo_sla: iso(0, slaHoras[pr]), resolvido_em: null, esta_atrasado: false, comentarios: [], created_at: iso(), updated_at: iso() };
        tickets.push(t);
        return { status: 201, data: t };
      }
      const t = achar(tickets, id(a), "Chamado");
      if (metodo === "patch") return { data: Object.assign(t, corpo, { updated_at: iso() }) };
      if (b === "assumir") { t.status = "em_andamento"; t.responsavel_id = (corpo.responsavel_id as number) ?? USUARIO_DEMO_ID; return { data: t }; }
      if (b === "resolver") { t.status = "resolvido"; t.resolvido_em = iso(); return { data: t }; }
      if (b === "cancelar") { t.status = "cancelado"; return { data: t }; }
      if (b === "comentarios") {
        const c = { id: nid(), ticket_id: t.id, created_by: USUARIO_DEMO_ID, mensagem: String(corpo.mensagem), created_at: iso() };
        t.comentarios.push(c);
        return { status: 201, data: c };
      }
    }
    if (recurso === "reunioes") {
      if (metodo === "get") return { data: [...reunioes].sort((x, y) => y.data_hora.localeCompare(x.data_hora)).filter((r) => !q("status") || r.status === q("status")) };
      if (metodo === "post" && !a) {
        const r: Reuniao = { id: nid(), predio_id: PREDIO_ID, tipo: corpo.tipo as Reuniao["tipo"], status: "convocada", titulo: String(corpo.titulo), data_hora: String(corpo.data_hora), local: String(corpo.local), pauta: String(corpo.pauta), ata: null, ata_registrada_em: null, ata_registrada_por: null, created_by: USUARIO_DEMO_ID, presencas: [], created_at: iso(), updated_at: iso() };
        reunioes.push(r);
        return { status: 201, data: r };
      }
      const r = achar(reunioes, id(a), "Reunião");
      const exigir = (acao: string) => { if (r.status !== "convocada") erro(409, `Só é possível ${acao} uma reunião com status 'convocada' (status atual: ${r.status}).`); };
      if (metodo === "patch") { exigir("editar"); return { data: Object.assign(r, corpo) }; }
      if (b === "cancelar") { exigir("cancelar"); r.status = "cancelada"; return { data: r }; }
      if (b === "ata") { exigir("registrar a ata de"); Object.assign(r, { ata: corpo.ata, status: "realizada", ata_registrada_em: iso(), ata_registrada_por: USUARIO_DEMO_ID }); return { data: r }; }
      if (b === "presenca" && metodo === "post") {
        exigir("confirmar presença em");
        if (r.presencas.some((x) => x.unidade_id === corpo.unidade_id)) erro(409, "Esta unidade já confirmou presença.");
        const pr = { id: nid(), reuniao_id: r.id, unidade_id: Number(corpo.unidade_id), created_by: USUARIO_DEMO_ID, created_at: iso() };
        r.presencas.push(pr);
        return { status: 201, data: pr };
      }
      if (b === "presenca" && metodo === "delete") { exigir("alterar a presença de"); r.presencas = r.presencas.filter((x) => x.unidade_id !== Number(seg[3])); return { status: 204 }; }
    }
    if (recurso === "entregas") {
      if (metodo === "get") return { data: ordenar(entregas).filter((e) => q("apenas_pendentes") !== "true" || !e.retirada_em) };
      if (metodo === "post" && !a) {
        const e: Entrega = { id: nid(), predio_id: PREDIO_ID, unidade_id: Number(corpo.unidade_id), descricao: String(corpo.descricao), localizacao: String(corpo.localizacao), retirada_em: null, retirada_por: null, created_by: USUARIO_DEMO_ID, created_at: iso(), updated_at: iso() };
        entregas.push(e);
        return { status: 201, data: e };
      }
      if (b === "retirar") { const e = achar(entregas, id(a), "Entrega"); if (e.retirada_em) erro(409, "Esta entrega já foi retirada."); Object.assign(e, { retirada_em: iso(), retirada_por: USUARIO_DEMO_ID }); return { data: e }; }
    }
    if (recurso === "visitantes") {
      if (metodo === "get") return { data: ordenar(visitantes) };
      const novo = (i: Json, unidade: number): Visitante => ({ id: nid(), predio_id: PREDIO_ID, unidade_id: unidade, nome_completo: String(i.nome_completo), tipo_documento: i.tipo_documento as Visitante["tipo_documento"], numero_documento: (i.numero_documento as string) ?? null, veiculo_placa: (i.veiculo_placa as string) ?? null, veiculo_modelo: (i.veiculo_modelo as string) ?? null, veiculo_cor: (i.veiculo_cor as string) ?? null, created_by: USUARIO_DEMO_ID, created_at: iso() });
      if (a === "lote") { const l = (corpo.visitantes as Json[]).map((i) => novo(i, Number(corpo.unidade_id))); visitantes.push(...l); return { status: 201, data: l }; }
      if (metodo === "post") { const v = novo(corpo, Number(corpo.unidade_id)); visitantes.push(v); return { status: 201, data: v }; }
    }
    if (recurso === "areas-comuns") {
      if (metodo === "get") return { data: areas.filter((x) => q("apenas_ativas") !== "true" || x.ativo) };
      if (metodo === "post" && !a) {
        const n: AreaComum = { id: nid(), predio_id: PREDIO_ID, nome: String(corpo.nome), descricao: (corpo.descricao as string) ?? null, capacidade: (corpo.capacidade as number) ?? null, ativo: true, agenda_liberada_ate: null, created_at: iso(), updated_at: iso() };
        areas.push(n);
        return { status: 201, data: n };
      }
      const ar = achar(areas, id(a), "Área");
      if (metodo === "patch") return { data: Object.assign(ar, corpo) };
      if (b === "liberar-agenda") { ar.agenda_liberada_ate = corpo.ate ? String(corpo.ate) : dia(Number(corpo.dias)); return { data: ar }; }
      if (metodo === "delete") { areas.splice(areas.indexOf(ar), 1); return { status: 204 }; }
    }
    if (recurso === "reservas") {
      if (metodo === "get") return { data: [...reservas].sort((x, y) => y.data.localeCompare(x.data)).filter((r) => !q("area_comum_id") || r.area_comum_id === Number(q("area_comum_id"))) };
      if (metodo === "post" && !a) {
        const ar = achar(areas, Number(corpo.area_comum_id), "Área");
        if (!ar.ativo) erro(409, "Esta área não está disponível para reserva.");
        if (String(corpo.data) < hoje) erro(422, "Não é possível reservar uma data no passado.");
        if (!ar.agenda_liberada_ate || String(corpo.data) > ar.agenda_liberada_ate) erro(409, "Esta data ainda não está liberada na agenda desta área.");
        if (reservas.some((r) => r.area_comum_id === ar.id && r.data === corpo.data && r.status === "confirmada")) erro(409, "Esta área já está reservada para esta data.");
        const n: Reserva = { id: nid(), predio_id: PREDIO_ID, area_comum_id: ar.id, unidade_id: Number(corpo.unidade_id ?? 1), data: String(corpo.data), status: "confirmada", observacoes: (corpo.observacoes as string) ?? null, cancelada_em: null, cancelada_por: null, created_by: USUARIO_DEMO_ID, created_at: iso() };
        reservas.push(n);
        return { status: 201, data: n };
      }
      if (b === "cancelar") { const r = achar(reservas, id(a), "Reserva"); if (r.status !== "confirmada") erro(409, "Esta reserva já está cancelada."); Object.assign(r, { status: "cancelada", cancelada_em: iso(), cancelada_por: USUARIO_DEMO_ID }); return { data: r }; }
    }
    if (recurso === "notificacoes") {
      if (a === "contagem-nao-lidas") return { data: { nao_lidas: notificacoes.filter((n) => !n.lida_em).length } };
      if (a === "marcar-todas-lidas") { notificacoes.forEach((n) => { n.lida_em ??= iso(); }); return { status: 204 }; }
      if (b === "marcar-lida") { const n = achar(notificacoes, id(a), "Notificação"); n.lida_em ??= iso(); return { data: n }; }
      if (metodo === "get") return { data: ordenar(notificacoes).filter((n) => q("apenas_nao_lidas") !== "true" || !n.lida_em) };
    }
    if (recurso === "fornecedores") {
      if (metodo === "get") return { data: fornecedores };
      const f: Fornecedor = { id: nid(), predio_id: PREDIO_ID, nome: String(corpo.nome), documento: null, cnpj: (corpo.cnpj as string) ?? null, razao_social: (corpo.razao_social as string) ?? null, nome_fantasia: (corpo.nome_fantasia as string) ?? null, categoria: String(corpo.categoria), telefone: null, email: null, observacoes: null, created_at: iso(), updated_at: iso(), deleted_at: null };
      fornecedores.push(f);
      return { status: 201, data: f };
    }
    if (recurso === "despesas-recorrentes") {
      if (a === "gerar-pendentes") {
        const gerados: DespesaLancamento[] = [];
        recorrentes.filter((r) => r.ativo).forEach((r) => {
          const alvo = hoje.slice(0, 8) + String(r.dia_vencimento).padStart(2, "0");
          if (alvo <= hoje && alvo >= r.data_inicio && (!r.ultima_geracao || r.ultima_geracao < alvo)) {
            const d = semRateio(nid(), r.descricao, r.categoria, r.valor, alvo, "pendente");
            d.observacoes = r.observacoes;
            despesas.push(d); gerados.push(d); r.ultima_geracao = alvo;
          }
        });
        return { data: gerados };
      }
      if (metodo === "get") return { data: recorrentes.filter((r) => q("incluir_inativas") === "true" || r.ativo) };
      if (metodo === "post") {
        const n: DespesaRecorrente = { id: nid(), predio_id: PREDIO_ID, fornecedor_id: (corpo.fornecedor_id as number) ?? null, unidade_id: null, descricao: String(corpo.descricao), categoria: String(corpo.categoria), valor: String(corpo.valor), dia_vencimento: Number(corpo.dia_vencimento), ativo: true, data_inicio: String(corpo.data_inicio), data_fim: (corpo.data_fim as string) ?? null, ultima_geracao: null, observacoes: null, created_at: iso(), updated_at: iso() };
        recorrentes.push(n);
        return { status: 201, data: n };
      }
      const r = achar(recorrentes, id(a), "Conta recorrente");
      if (metodo === "patch") return { data: Object.assign(r, corpo) };
      if (metodo === "delete") { recorrentes.splice(recorrentes.indexOf(r), 1); return { status: 204 }; }
    }
    if (recurso === "despesas") {
      if (a === "ocr/extrair" || (a === "ocr" && b === "extrair")) {
        return { data: { documento_url: "demo/boleto.pdf", fornecedor_nome: "Companhia de Saneamento", fornecedor_documento: "43776517000180", valor: "2140.35", data_vencimento: dia(12), linha_digitavel: "82640000021 4 03500000019 0 00000000001 2 50120000000 3", descricao_sugerida: "Conta de água", categoria_sugerida: "agua" } };
      }
      if (metodo === "get" && !a) return { data: ordenar(despesas) };
      if (metodo === "post" && !a) {
        const d = semRateio(nid(), String(corpo.descricao), String(corpo.categoria), String(corpo.valor), String(corpo.data_vencimento), "pendente");
        d.observacoes = (corpo.observacoes as string) ?? null;
        d.documento_url = (corpo.documento_url as string) ?? null;
        despesas.push(d);
        return { status: 201, data: d };
      }
      const d = achar(despesas, id(a), "Conta");
      if (metodo === "patch") return { data: Object.assign(d, corpo) };
      if (b === "pagar") { if (d.status !== "pendente") erro(409, "Só é possível pagar uma conta pendente."); Object.assign(d, { status: "pago", data_pagamento: hoje }); return { data: d }; }
      if (b === "desfazer-pagamento") { Object.assign(d, { status: "pendente", data_pagamento: null, comprovante_pagamento_url: null }); return { data: d }; }
      if (b === "cancelar") { d.status = "cancelado"; return { data: d }; }
      if (b === "ratear") { ratear(d, (corpo.criterio as "igual" | "fracao_ideal") ?? "igual"); return { data: d }; }
      if (b === "comprovante") { d.comprovante_pagamento_url = form ? "demo/comprovante.txt" : null; return { data: d }; }
    }
    if (recurso === "transparencia") {
      const ano = q("ano") ? Number(q("ano")) : undefined;
      const mes = q("mes") ? Number(q("mes")) : undefined;
      if (a === "balancete" && b === "serie") {
        const n = Number(q("meses") ?? 6);
        const serie = Array.from({ length: n }, (_, k) => {
          const dt = new Date(); dt.setDate(1); dt.setMonth(dt.getMonth() - (n - 1 - k));
          const bal = balancete(dt.getFullYear(), dt.getMonth() + 1);
          return { ano: dt.getFullYear(), mes: dt.getMonth() + 1, total_pago: bal.total_pago, total_pendente: bal.total_pendente, total_geral: bal.total_geral };
        });
        return { data: serie };
      }
      if (a === "balancete") return { data: balancete(ano, mes) };
      if (a === "despesas") {
        return { data: ordenar(despesas).filter((d) => {
          const dt = new Date(`${d.data_vencimento}T00:00:00`);
          return (!ano || dt.getFullYear() === ano) && (!mes || dt.getMonth() + 1 === mes);
        }).map((d) => ({ id: d.id, unidade_id: d.unidade_id, descricao: d.descricao, categoria: d.categoria, valor: d.valor, data_vencimento: d.data_vencimento, data_pagamento: d.data_pagamento, status: d.status, esta_atrasada: d.esta_atrasada, documento_url: d.documento_url, comprovante_pagamento_url: d.comprovante_pagamento_url })) };
      }
      if (a === "previa-unidade") {
        const uid = Number(q("unidade_id") ?? 1);
        const itens = despesas.filter((d) => {
          const dt = new Date(`${d.data_vencimento}T00:00:00`);
          return d.status !== "cancelado" && (!ano || dt.getFullYear() === ano) && (!mes || dt.getMonth() + 1 === mes) && (d.unidade_id == null || d.unidade_id === uid);
        }).map((d) => ({ despesa_id: d.id, descricao: d.descricao, categoria: d.categoria, tipo: (d.unidade_id == null ? "rateio" : "multa") as "rateio" | "multa", valor: d.unidade_id == null ? (Number(d.valor) / nUnidades).toFixed(2) : d.valor, status: d.status, data_vencimento: d.data_vencimento }));
        const s = (t: string) => itens.filter((i) => i.tipo === t).reduce((x, i) => x + Number(i.valor), 0);
        return { data: { unidade_id: uid, ano: ano ?? new Date().getFullYear(), mes: mes ?? null, total_rateio: s("rateio").toFixed(2), total_multas: s("multa").toFixed(2), total_geral: (s("rateio") + s("multa")).toFixed(2), itens } };
      }
    }
    return erro(404, "Recurso não simulado na prévia.");
  }

  return { rota };
}

export function criarAdapterFalso(): AxiosAdapter {
  const { rota } = criarBackendFalso();

  return async (config: InternalAxiosRequestConfig): Promise<AxiosResponse> => {
    const metodo = (config.method ?? "get").toLowerCase();
    const url = (config.url ?? "").split("?")[0];
    const form = typeof FormData !== "undefined" && config.data instanceof FormData ? config.data : null;
    let corpo: Json = {};
    if (!form && typeof config.data === "string" && config.data) {
      try { corpo = JSON.parse(config.data) as Json; } catch { corpo = {}; }
    }
    const resposta = (status: number, data: unknown): AxiosResponse => ({ data, status, statusText: String(status), headers: {}, config });

    await new Promise((r) => setTimeout(r, 120));

    if (config.responseType === "blob") {
      return resposta(200, new Blob(["Documento de demonstração - nenhum arquivo real foi enviado."], { type: "text/plain" }));
    }
    try {
      const r = rota(metodo, url, (config.params ?? {}) as Json, corpo, form);
      return resposta(r.status ?? 200, r.data === undefined ? "" : JSON.parse(JSON.stringify(r.data)));
    } catch (e) {
      const d = e as { __demoErro?: boolean; status: number; detail: string };
      if (!d.__demoErro) throw e;
      const res = resposta(d.status, { detail: d.detail });
      throw new AxiosError(d.detail, String(d.status), config, null, res);
    }
  };
}
