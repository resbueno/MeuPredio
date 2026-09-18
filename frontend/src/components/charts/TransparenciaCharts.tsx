import { useState } from "react";

const AZUL = "#2a78d6";
const TEXTO_SECUNDARIO = "#52514e";
const TEXTO_MUTED = "#8a8a86";
const GRADE = "#e4e3df";

function formatarMoeda(valor: number): string {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

interface ItemCategoria {
  categoria: string;
  total: number;
}

/** Barras horizontais por categoria - magnitude, nao identidade (as
 * categorias sao texto livre do usuario, nao uma serie fixa que reaparece
 * em outros graficos), por isso um unico tom sequencial em vez de cores
 * categoricas. */
export function GraficoCategoria({ itens }: { itens: ItemCategoria[] }) {
  const [hover, setHover] = useState<number | null>(null);
  if (itens.length === 0) return null;

  const maximo = Math.max(...itens.map((i) => i.total), 1);
  const ordenados = [...itens].sort((a, b) => b.total - a.total);
  const alturaBarra = 22;
  const espacamento = 10;
  const alturaTotal = ordenados.length * (alturaBarra + espacamento) - espacamento;
  const larguraLabel = 92;
  const larguraGrafico = 240;

  return (
    <div className="overflow-x-auto">
      <svg
        width="100%"
        viewBox={`0 0 ${larguraLabel + larguraGrafico + 60} ${alturaTotal}`}
        role="img"
        aria-label="Gastos por categoria no período"
        className="min-w-[320px]"
      >
        {ordenados.map((item, indice) => {
          const y = indice * (alturaBarra + espacamento);
          const largura = Math.max((item.total / maximo) * larguraGrafico, 2);
          const emHover = hover === indice;
          return (
            <g key={item.categoria}>
              <text
                x={larguraLabel - 8}
                y={y + alturaBarra / 2}
                textAnchor="end"
                dominantBaseline="middle"
                fontSize="12"
                fill={TEXTO_SECUNDARIO}
                className="capitalize"
              >
                {item.categoria}
              </text>
              <rect
                x={larguraLabel}
                y={y}
                width={larguraGrafico}
                height={alturaBarra}
                fill={GRADE}
                opacity={0.4}
                rx={4}
              />
              <rect
                x={larguraLabel}
                y={y}
                width={largura}
                height={alturaBarra}
                fill={AZUL}
                opacity={emHover ? 1 : 0.85}
                rx={4}
                onMouseEnter={() => setHover(indice)}
                onMouseLeave={() => setHover(null)}
              >
                <title>{`${item.categoria}: ${formatarMoeda(item.total)}`}</title>
              </rect>
              <text
                x={larguraLabel + largura + 8}
                y={y + alturaBarra / 2}
                dominantBaseline="middle"
                fontSize="12"
                fontWeight={emHover ? 700 : 500}
                fill={TEXTO_SECUNDARIO}
              >
                {formatarMoeda(item.total)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

interface PontoSerie {
  ano: number;
  mes: number;
  total_geral: number;
}

const MESES_ABREV = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];

/** Linha de tendencia (serie unica) - sem legenda (uma so cor, o titulo ja
 * diz o que e), com um crosshair simples no hover mostrando mes+valor. */
export function GraficoTendencia({ pontos }: { pontos: PontoSerie[] }) {
  const [hover, setHover] = useState<number | null>(null);
  if (pontos.length < 2) return null;

  const largura = 320;
  const altura = 120;
  const margemEsquerda = 8;
  const margemInferior = 20;
  const valores = pontos.map((p) => p.total_geral);
  const maximo = Math.max(...valores, 1);

  const passoX = (largura - margemEsquerda * 2) / (pontos.length - 1);
  const coordenadas = pontos.map((ponto, indice) => ({
    x: margemEsquerda + indice * passoX,
    y: altura - margemInferior - (ponto.total_geral / maximo) * (altura - margemInferior - 10),
    ponto,
  }));

  const caminho = coordenadas.map((c, i) => `${i === 0 ? "M" : "L"} ${c.x} ${c.y}`).join(" ");

  return (
    <div className="overflow-x-auto">
      <svg
        width="100%"
        viewBox={`0 0 ${largura} ${altura}`}
        role="img"
        aria-label="Tendência de gastos nos últimos meses"
        className="min-w-[280px]"
      >
        <line
          x1={margemEsquerda}
          y1={altura - margemInferior}
          x2={largura - margemEsquerda}
          y2={altura - margemInferior}
          stroke={GRADE}
          strokeWidth={1}
        />
        <path d={caminho} fill="none" stroke={AZUL} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
        {coordenadas.map((c, indice) => (
          <g key={`${c.ponto.ano}-${c.ponto.mes}`}>
            <circle
              cx={c.x}
              cy={c.y}
              r={hover === indice ? 6 : 4}
              fill={AZUL}
              stroke="#ffffff"
              strokeWidth={2}
              onMouseEnter={() => setHover(indice)}
              onMouseLeave={() => setHover(null)}
              style={{ cursor: "pointer" }}
            >
              <title>{`${MESES_ABREV[c.ponto.mes - 1]}/${c.ponto.ano}: ${formatarMoeda(c.ponto.total_geral)}`}</title>
            </circle>
            <text
              x={c.x}
              y={altura - 4}
              textAnchor="middle"
              fontSize="10"
              fill={TEXTO_MUTED}
            >
              {MESES_ABREV[c.ponto.mes - 1]}
            </text>
          </g>
        ))}
        {hover !== null && (
          <text
            x={coordenadas[hover].x}
            y={Math.max(coordenadas[hover].y - 10, 10)}
            textAnchor="middle"
            fontSize="11"
            fontWeight={700}
            fill={TEXTO_SECUNDARIO}
          >
            {formatarMoeda(coordenadas[hover].ponto.total_geral)}
          </text>
        )}
      </svg>
    </div>
  );
}
