import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useLocation, useNavigate, type Location } from "react-router-dom";
import { z } from "zod";
import axios from "axios";
import { useAuth } from "../auth/AuthContext";
import { identificarPredio } from "../api/predios";
import type { PredioIdentificado } from "../api/types";
import logoFull from "../assets/logo-full.png";

const predioSchema = z.object({
  cep: z
    .string()
    .min(1, "Informe o CEP.")
    .regex(/^\d{5}-?\d{3}$/, "CEP invalido (formato 00000-000)."),
  numero: z.string().min(1, "Informe o numero do predio."),
});

type PredioFormValues = z.infer<typeof predioSchema>;

const credenciaisSchema = z.object({
  email: z.string().min(1, "Informe o e-mail.").email("Informe um e-mail valido."),
  password: z.string().min(1, "Informe a senha."),
});

type CredenciaisFormValues = z.infer<typeof credenciaisSchema>;

interface LocationState {
  from?: Location;
}

function MailIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 6.75A2.25 2.25 0 0 1 5.25 4.5h13.5A2.25 2.25 0 0 1 21 6.75v10.5A2.25 2.25 0 0 1 18.75 19.5H5.25A2.25 2.25 0 0 1 3 17.25V6.75Z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="m3.5 7 8.5 6 8.5-6" />
    </svg>
  );
}

function LockIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 10.5V7.125a4.5 4.5 0 1 1 9 0V10.5" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 10.5h12a1.5 1.5 0 0 1 1.5 1.5v7.5A1.5 1.5 0 0 1 18 21H6a1.5 1.5 0 0 1-1.5-1.5V12A1.5 1.5 0 0 1 6 10.5Z" />
    </svg>
  );
}

function BuildingIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 21V5.25A1.5 1.5 0 0 1 5.5 3.75h7A1.5 1.5 0 0 1 14 5.25V21" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M14 21V9.75a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1V21" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M7 7.5h1M10 7.5h1M7 11h1M10 11h1M7 14.5h1M10 14.5h1M16 13h1M16 16.5h1" />
    </svg>
  );
}

function HashIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 4 7 20M17 4l-2 16M4.5 9h15M3.5 15h15" />
    </svg>
  );
}

function EyeIcon({ open }: { open: boolean }) {
  if (open) {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-5 w-5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 3l18 18M10.58 10.58a2 2 0 0 0 2.83 2.83M9.88 4.62A9.77 9.77 0 0 1 12 4.5c5 0 9 4.5 9 7.5-1 1.96-2.55 3.6-4.36 4.7M6.6 6.6C4.6 7.9 3 9.9 3 12c0 3 4 7.5 9 7.5 1.06 0 2.06-.19 3-.53" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12S5.5 5.25 12 5.25 21.75 12 21.75 12 18.5 18.75 12 18.75 2.25 12 2.25 12Z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" />
    </svg>
  );
}

/** Cartão branco compartilhado pelas duas etapas - só o conteúdo muda. */
function Cartao({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white p-6 shadow-2xl shadow-black/40 sm:p-8">
      {children}
    </div>
  );
}

export function Login() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Login em 2 etapas (ver conversa com o cliente): 1) identificar o prédio
  // por CEP+número - isso escopa tudo ao que segue; 2) e-mail/senha DENTRO
  // daquele prédio. "Sou administrador" pula direto para a etapa 2, sem
  // prédio - é o único papel que não pertence a nenhum (ver backend).
  const [predio, setPredio] = useState<PredioIdentificado | null>(null);
  const [modoAdmin, setModoAdmin] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const etapaCredenciais = predio !== null || modoAdmin;

  const predioForm = useForm<PredioFormValues>({ resolver: zodResolver(predioSchema) });
  const credenciaisForm = useForm<CredenciaisFormValues>({ resolver: zodResolver(credenciaisSchema) });

  async function onSubmitPredio(values: PredioFormValues): Promise<void> {
    setServerError(null);
    try {
      const encontrado = await identificarPredio(values.cep.replace("-", ""), values.numero);
      setPredio(encontrado);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 404) {
        setServerError("Nenhum predio encontrado para este CEP e numero.");
      } else {
        setServerError("Nao foi possivel verificar o predio agora. Tente novamente.");
      }
    }
  }

  async function onSubmitCredenciais(values: CredenciaisFormValues): Promise<void> {
    setServerError(null);
    try {
      await signIn(values.email, values.password, modoAdmin ? null : predio!.id);
      const state = location.state as LocationState | null;
      const destino = state?.from?.pathname ?? "/";
      navigate(destino, { replace: true });
    } catch {
      setServerError("E-mail ou senha invalidos.");
    }
  }

  function voltar(): void {
    setPredio(null);
    setModoAdmin(false);
    setServerError(null);
    credenciaisForm.reset();
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-ink px-4 py-10">
      {/* Glows decorativos de fundo — só estética, não interferem no conteúdo. */}
      <div className="pointer-events-none absolute -left-24 -top-24 h-72 w-72 rounded-full bg-brand-600/30 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-24 -right-16 h-80 w-80 rounded-full bg-brand-400/20 blur-3xl" />

      <div className="relative w-full max-w-sm">
        <div className="mb-6 flex justify-center">
          <img
            src={logoFull}
            alt="MeuPrédio"
            className="w-44 rounded-2xl bg-white/95 p-4 shadow-xl shadow-black/30"
          />
        </div>

        {!etapaCredenciais && (
          <Cartao>
            <h1 className="text-xl font-bold text-ink">Qual e o seu predio?</h1>
            <p className="mb-6 mt-1 text-sm text-slate-500">
              Informe o CEP e o numero do predio para continuar.
            </p>

            <form
              onSubmit={predioForm.handleSubmit(onSubmitPredio)}
              className="space-y-4"
              noValidate
            >
              <div>
                <label htmlFor="cep" className="mb-1 block text-sm font-medium text-slate-700">
                  CEP
                </label>
                <div className="relative">
                  <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-slate-400">
                    <BuildingIcon />
                  </span>
                  <input
                    id="cep"
                    inputMode="numeric"
                    autoComplete="postal-code"
                    placeholder="00000-000"
                    className="w-full rounded-xl border border-slate-300 py-2.5 pl-10 pr-3 text-base text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
                    {...predioForm.register("cep")}
                  />
                </div>
                {predioForm.formState.errors.cep && (
                  <p className="mt-1 text-sm text-red-600">
                    {predioForm.formState.errors.cep.message}
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="numero" className="mb-1 block text-sm font-medium text-slate-700">
                  Numero do predio
                </label>
                <div className="relative">
                  <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-slate-400">
                    <HashIcon />
                  </span>
                  <input
                    id="numero"
                    placeholder="Ex.: 1000"
                    className="w-full rounded-xl border border-slate-300 py-2.5 pl-10 pr-3 text-base text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
                    {...predioForm.register("numero")}
                  />
                </div>
                {predioForm.formState.errors.numero && (
                  <p className="mt-1 text-sm text-red-600">
                    {predioForm.formState.errors.numero.message}
                  </p>
                )}
              </div>

              {serverError && (
                <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{serverError}</p>
              )}

              <button
                type="submit"
                disabled={predioForm.formState.isSubmitting}
                className="w-full rounded-xl bg-brand-600 px-4 py-2.5 text-base font-semibold text-white shadow-lg shadow-brand-600/30 transition hover:bg-brand-700 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {predioForm.formState.isSubmitting ? "Verificando..." : "Continuar"}
              </button>

              <button
                type="button"
                onClick={() => setModoAdmin(true)}
                className="w-full text-center text-xs font-medium text-slate-400 hover:text-slate-600"
              >
                Sou administrador do sistema
              </button>
            </form>
          </Cartao>
        )}

        {etapaCredenciais && (
          <Cartao>
            <button
              type="button"
              onClick={voltar}
              className="mb-3 flex items-center gap-1 text-xs font-medium text-slate-400 hover:text-slate-600"
            >
              ← Trocar predio
            </button>

            <h1 className="text-xl font-bold text-ink">Entrar</h1>
            <p className="mb-6 mt-1 text-sm text-slate-500">
              {modoAdmin ? (
                "Acesso do administrador do sistema."
              ) : (
                <>
                  Entrando em <span className="font-semibold text-slate-700">{predio?.nome}</span>
                  {predio?.cidade && ` · ${predio.cidade}${predio.uf ? `/${predio.uf}` : ""}`}
                </>
              )}
            </p>

            <form
              onSubmit={credenciaisForm.handleSubmit(onSubmitCredenciais)}
              className="space-y-4"
              noValidate
            >
              <div>
                <label htmlFor="email" className="mb-1 block text-sm font-medium text-slate-700">
                  E-mail
                </label>
                <div className="relative">
                  <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-slate-400">
                    <MailIcon />
                  </span>
                  <input
                    id="email"
                    type="email"
                    autoComplete="username"
                    placeholder="voce@exemplo.com"
                    className="w-full rounded-xl border border-slate-300 py-2.5 pl-10 pr-3 text-base text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
                    {...credenciaisForm.register("email")}
                  />
                </div>
                {credenciaisForm.formState.errors.email && (
                  <p className="mt-1 text-sm text-red-600">
                    {credenciaisForm.formState.errors.email.message}
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="password" className="mb-1 block text-sm font-medium text-slate-700">
                  Senha
                </label>
                <div className="relative">
                  <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-slate-400">
                    <LockIcon />
                  </span>
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    placeholder="••••••••"
                    className="w-full rounded-xl border border-slate-300 py-2.5 pl-10 pr-10 text-base text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
                    {...credenciaisForm.register("password")}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    className="absolute inset-y-0 right-3 flex items-center text-slate-400 hover:text-slate-600"
                    aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                  >
                    <EyeIcon open={showPassword} />
                  </button>
                </div>
                {credenciaisForm.formState.errors.password && (
                  <p className="mt-1 text-sm text-red-600">
                    {credenciaisForm.formState.errors.password.message}
                  </p>
                )}
              </div>

              {serverError && (
                <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{serverError}</p>
              )}

              <button
                type="submit"
                disabled={credenciaisForm.formState.isSubmitting}
                className="w-full rounded-xl bg-brand-600 px-4 py-2.5 text-base font-semibold text-white shadow-lg shadow-brand-600/30 transition hover:bg-brand-700 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {credenciaisForm.formState.isSubmitting ? "Entrando..." : "Entrar"}
              </button>
            </form>
          </Cartao>
        )}

        <p className="mt-6 text-center text-xs text-slate-400">
          MeuPrédio · gestão de condomínios
        </p>
      </div>
    </div>
  );
}
