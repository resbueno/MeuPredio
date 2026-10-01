import { useEffect, useState, type ReactNode } from "react";
import { ChevronDown, Menu, X } from "lucide-react";
import logoIcon from "../../assets/logo-icon.png";
import fotoCidade from "../../assets/landing-hero.jpg";

// Alturas decorativas das barras do gráfico (sem significado numérico real).
const BAR_HEIGHTS = [
  23, 40, 53, 40, 33, 14, 7, 17, 75, 65, 88, 75, 65, 47, 33, 88, 4, 7, 9, 14, 95, 65, 79, 37, 7, 40, 17, 20, 62, 47,
  92, 72,
];

const DIRECTION_CLASS: Record<"up" | "down" | "left" | "right" | "scale", string> = {
  up: "animate-fade-up",
  down: "animate-fade-down",
  left: "animate-fade-left",
  right: "animate-fade-right",
  scale: "animate-fade-scale",
};

function Animate({
  children,
  delay = 0,
  className = "",
  direction = "up",
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
  direction?: "up" | "down" | "left" | "right" | "scale";
}) {
  return (
    <div className={`opacity-0 ${DIRECTION_CLASS[direction]} ${className}`} style={{ animationDelay: `${delay}ms` }}>
      {children}
    </div>
  );
}

function StatsCard() {
  const maxHeight = Math.max(...BAR_HEIGHTS);
  const axisLabels = ["Jan", "Mar", "Mai", "Jul", "Set"];

  return (
    <Animate delay={900} direction="scale" className="w-full max-w-[405px] mx-auto lg:mx-0">
      <div className="w-full rounded-[24px] sm:rounded-[33px] bg-[rgba(17,16,15,0.35)] backdrop-blur-[20px] p-5 sm:p-8 pb-5 sm:pb-6">
        <p className="text-white text-[16px] sm:text-[20px] font-[450] leading-[20px] mb-3 sm:mb-4">
          Valor administrado na plataforma
        </p>

        <p className="mb-2 sm:mb-3">
          <span className="text-white text-[28px] sm:text-[46px] font-[450] leading-[1]">R$14.205.890</span>
          <span className="text-white/20 text-[28px] sm:text-[46px] font-[450] leading-[1]">,00</span>
        </p>

        <div className="flex items-center gap-[10px] mb-6 sm:mb-8">
          <span className="px-[6px] py-[7px] bg-white/20 rounded-[6px] text-white text-[12px] sm:text-[14px] font-[450] leading-[14px]">
            +32,4%
          </span>
          <span className="text-white/80 text-[12px] sm:text-[14px] font-[450] leading-[14px] opacity-70">
            vs. período anterior (R$10,7M)
          </span>
        </div>

        <div className="relative">
          <div className="flex items-end gap-[1.5px] h-[80px] sm:h-[100px]">
            {BAR_HEIGHTS.map((h, i) => {
              const isProjected = i >= 28;
              const heightPercent = (h / maxHeight) * 100;
              return (
                <div
                  key={i}
                  className="flex-1 rounded-[0.5px] animate-bar-grow origin-bottom"
                  style={{
                    height: `${heightPercent}%`,
                    backgroundColor: isProjected ? "rgba(255,255,255,0.1)" : "white",
                    animationDelay: `${1100 + i * 30}ms`,
                  }}
                />
              );
            })}
          </div>

          <div className="absolute inset-0 pointer-events-none">
            {[0, 1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="absolute top-0 bottom-0 w-px bg-white/10"
                style={{ left: `${((i + 1) / 5) * 100}%` }}
              />
            ))}
          </div>

          <div className="flex justify-between mt-3">
            {axisLabels.map((label, i) => (
              <span
                key={label + i}
                className="text-[9px] sm:text-[10px] font-[450] leading-[10px] text-white/80"
                style={{ opacity: i >= 3 ? 0.4 : 1 }}
              >
                {label}
              </span>
            ))}
          </div>
        </div>
      </div>
    </Animate>
  );
}

export default function ApogeeHero({
  onConhecerAgora,
  onFalarComEquipe,
  onEntrar,
}: {
  onConhecerAgora: () => void;
  onFalarComEquipe: () => void;
  onEntrar: () => void;
}) {
  return (
    <section
      className="relative w-full h-screen overflow-hidden bg-[#080A19]"
      style={{ fontFamily: "'Suisse Int\\'l', -apple-system, BlinkMacSystemFont, sans-serif" }}
    >
      <img
        className="absolute inset-0 w-full h-full object-cover"
        src={fotoCidade}
        alt="Skyline de um condomínio residencial iluminado à noite"
      />

      <div className="relative z-10 h-full flex flex-col">
        <Nav onConhecerAgora={onConhecerAgora} onEntrar={onEntrar} />

        <div className="flex-1 flex items-center py-8">
          <div className="w-full max-w-[1800px] mx-auto px-5 sm:px-8 md:px-[82px] flex flex-col lg:flex-row lg:items-center lg:justify-between gap-10 lg:gap-12">
            <div className="max-w-[593px]">
              <Animate delay={300} direction="up">
                <h1 className="text-white text-[36px] sm:text-[52px] md:text-[64px] lg:text-[72px] font-normal leading-[0.95] mb-5 sm:mb-8">
                  Eleve a gestão do seu prédio a um novo patamar
                </h1>
              </Animate>

              <Animate delay={500} direction="up">
                <p className="text-white/80 text-[16px] sm:text-[18px] md:text-[20px] font-[450] leading-[1.3] max-w-[370px] mb-7 sm:mb-10">
                  Portal da transparência, boletos com leitura por IA e gestão condominial pensada para o seu dia a
                  dia
                </p>
              </Animate>

              <Animate delay={700} direction="up">
                <div className="flex flex-wrap gap-3 sm:gap-4">
                  <button
                    type="button"
                    onClick={onConhecerAgora}
                    className="h-[46px] sm:h-[51px] px-5 sm:px-[27px] bg-[#E9E9E9] rounded-[12px] text-[#0A0707] text-[14px] sm:text-[15.5px] font-[450] leading-[15.5px] transition-opacity hover:opacity-90"
                  >
                    Conheça o Meu Prédio
                  </button>
                  <button
                    type="button"
                    onClick={onFalarComEquipe}
                    className="h-[46px] sm:h-[51px] px-5 sm:px-[27px] rounded-[12px] border border-white text-white text-[14px] sm:text-[15.5px] font-[450] leading-[15.5px] transition-opacity hover:opacity-80"
                  >
                    Falar com a equipe
                  </button>
                </div>
              </Animate>
            </div>

            <StatsCard />
          </div>
        </div>
      </div>
    </section>
  );
}

function Nav({ onConhecerAgora, onEntrar }: { onConhecerAgora: () => void; onEntrar: () => void }) {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  const linkClass =
    "flex items-center justify-between px-4 py-4 rounded-[12px] text-white/90 text-[18px] font-[450] hover:bg-white/[0.06] transition-all duration-300";
  const panelLinks = [
    { label: "Recursos", href: "#recursos" },
    { label: "Como funciona", href: "#como-funciona" },
    { label: "Contato", href: "#contato" },
  ];

  return (
    <>
      <nav className="w-full max-w-[1800px] mx-auto px-5 sm:px-8 md:px-[82px] pt-[20px] sm:pt-[30px] flex items-center justify-between relative z-50">
        <Animate delay={0} direction="down">
          <div className="flex items-center gap-2.5">
            <img src={logoIcon} alt="" className="w-[28px] h-[28px] sm:w-[32px] sm:h-[32px]" />
            <span className="text-white text-[22px] sm:text-[26px] font-[450] leading-none tracking-[-0.02em]">
              Meu<span className="opacity-80">Prédio</span>
            </span>
          </div>
        </Animate>

        <Animate delay={100} direction="down" className="hidden lg:block">
          <div className="h-[52px] px-6 flex items-center gap-[30px] bg-[rgba(10,7,7,0.35)] rounded-[11px] backdrop-blur-[17px]">
            <button
              type="button"
              className="flex items-center gap-[5px] text-white/80 text-[14px] font-[450] leading-[14px] hover:text-white transition-colors"
            >
              Recursos
              <ChevronDown className="w-[10px] h-[10px] opacity-80" />
            </button>
            <a
              href="#como-funciona"
              className="text-white/80 text-[14px] font-[450] leading-[14px] hover:text-white transition-colors cursor-pointer"
            >
              Como funciona
            </a>
            <a
              href="#contato"
              className="text-white/80 text-[14px] font-[450] leading-[14px] hover:text-white transition-colors cursor-pointer"
            >
              Contato
            </a>
          </div>
        </Animate>

        <Animate delay={200} direction="down" className="hidden lg:block">
          <div className="h-[52px] p-[3px] bg-[rgba(0,0,0,0.35)] rounded-[13px] backdrop-blur-[17px] flex items-center gap-[5px]">
            <button
              type="button"
              onClick={onEntrar}
              className="h-[46px] px-6 rounded-[11px] text-white text-[14px] font-[450] leading-[14px] hover:bg-white/5 transition-colors"
            >
              Entrar
            </button>
            <button
              type="button"
              onClick={onConhecerAgora}
              className="h-[46px] px-6 bg-[#E9E9E9] rounded-[11px] text-[#0A0707] text-[14px] font-[450] leading-[14px] hover:bg-white transition-colors"
            >
              Conhecer agora
            </button>
          </div>
        </Animate>

        <Animate delay={100} direction="down" className="lg:hidden">
          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            aria-label="Alternar menu"
            className="w-[44px] h-[44px] flex items-center justify-center rounded-[11px] bg-[rgba(10,7,7,0.35)] backdrop-blur-[17px] transition-colors hover:bg-white/10"
          >
            <div className="relative w-5 h-5">
              <Menu
                className={`w-5 h-5 text-white absolute inset-0 transition-all duration-300 ease-out ${
                  isOpen ? "opacity-0 rotate-90 scale-75" : "opacity-100 rotate-0 scale-100"
                }`}
              />
              <X
                className={`w-5 h-5 text-white absolute inset-0 transition-all duration-300 ease-out ${
                  isOpen ? "opacity-100 rotate-0 scale-100" : "opacity-0 -rotate-90 scale-75"
                }`}
              />
            </div>
          </button>
        </Animate>
      </nav>

      <div
        className={`lg:hidden fixed inset-0 z-40 transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] ${
          isOpen ? "visible" : "invisible"
        }`}
      >
        <div
          onClick={() => setIsOpen(false)}
          className={`absolute inset-0 bg-[#080A19]/90 backdrop-blur-[24px] transition-opacity duration-500 ${
            isOpen ? "opacity-100" : "opacity-0"
          }`}
        />

        <div
          className={`absolute top-[76px] sm:top-[86px] left-4 right-4 sm:left-6 sm:right-6 bg-[rgba(17,16,15,0.6)] backdrop-blur-[30px] rounded-[20px] border border-white/[0.06] p-6 sm:p-8 transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] origin-top ${
            isOpen ? "opacity-100 translate-y-0 scale-100" : "opacity-0 -translate-y-4 scale-[0.97]"
          }`}
        >
          <div className="flex flex-col gap-1">
            {panelLinks.map((item, i) => (
              <a
                key={item.label}
                href={item.href}
                onClick={() => setIsOpen(false)}
                className={`${linkClass} ${isOpen ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-3"}`}
                style={{ transitionDelay: isOpen ? `${100 + i * 50}ms` : "0ms" }}
              >
                {item.label}
                {item.label === "Recursos" && <ChevronDown className="w-4 h-4 opacity-50" />}
              </a>
            ))}
          </div>

          <div className="h-px bg-white/10 my-5" />

          <div
            className={`flex flex-col gap-3 transition-all duration-300 ${
              isOpen ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"
            }`}
            style={{ transitionDelay: isOpen ? "350ms" : "0ms" }}
          >
            <button
              type="button"
              onClick={() => {
                setIsOpen(false);
                onConhecerAgora();
              }}
              className="w-full h-[50px] bg-[#E9E9E9] rounded-[12px] text-[#0A0707] text-[15px] font-[450] transition-colors hover:bg-white"
            >
              Conhecer agora
            </button>
            <button
              type="button"
              onClick={() => {
                setIsOpen(false);
                onEntrar();
              }}
              className="w-full h-[50px] rounded-[12px] border border-white/30 text-white text-[15px] font-[450] transition-colors hover:bg-white/5"
            >
              Entrar
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
