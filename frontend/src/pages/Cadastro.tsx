import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, useParams } from "react-router-dom";
import { z } from "zod";
import axios from "axios";
import { cadastrarViaConvite, obterInfoConvite } from "../api/predios";
import logoFull from "../assets/logo-full.png";

const cadastroSchema = z.object({
  full_name: z.string().min(2, "Informe o nome completo."),
  email: z.string().min(1, "Informe o e-mail.").email("Informe um e-mail valido."),
  password: z.string().min(8, "A senha deve ter ao menos 8 caracteres."),
  role: z.enum(["morador", "proprietario"]),
  unidade_ids: z.array(z.number()).min(1, "Selecione ao menos uma unidade."),
});

type CadastroFormValues = z.infer<typeof cadastroSchema>;

export function Cadastro() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState(false);

  const { data: info, isLoading, isError } = useQuery({
    queryKey: ["convite", token],
    queryFn: () => obterInfoConvite(token!),
    enabled: Boolean(token),
    retry: false,
  });

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<CadastroFormValues>({
    resolver: zodResolver(cadastroSchema),
    defaultValues: { role: "morador", unidade_ids: [] },
  });

  const unidadeIdsSelecionadas = watch("unidade_ids");

  const mutation = useMutation({
    mutationFn: (values: CadastroFormValues) => cadastrarViaConvite(token!, values),
    onSuccess: () => setSucesso(true),
    onError: (err) => {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        setServerError("Ja existe um cadastro com este e-mail neste predio.");
      } else {
        setServerError("Nao foi possivel concluir o cadastro. Verifique os dados e tente novamente.");
      }
    },
  });

  function toggleUnidade(id: number): void {
    const atual = unidadeIdsSelecionadas ?? [];
    setValue(
      "unidade_ids",
      atual.includes(id) ? atual.filter((u) => u !== id) : [...atual, id],
      { shouldValidate: true }
    );
  }

  function onSubmit(values: CadastroFormValues): void {
    setServerError(null);
    mutation.mutate(values);
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-ink px-4 py-10">
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

        <div className="rounded-2xl border border-white/10 bg-white p-6 shadow-2xl shadow-black/40 sm:p-8">
          {isLoading && <p className="text-sm text-slate-500">Carregando convite...</p>}

          {isError && (
            <div className="text-center">
              <h1 className="text-lg font-bold text-ink">Convite invalido</h1>
              <p className="mt-2 text-sm text-slate-500">
                Este link de cadastro nao existe mais, expirou ou foi revogado. Peca um novo
                convite ao sindico ou administrador do seu predio.
              </p>
            </div>
          )}

          {sucesso && (
            <div className="text-center">
              <h1 className="text-lg font-bold text-ink">Cadastro concluido!</h1>
              <p className="mt-2 text-sm text-slate-500">
                Sua conta foi criada. Agora e so entrar com seu e-mail e senha.
              </p>
              <button
                type="button"
                onClick={() => navigate("/login", { replace: true })}
                className="mt-6 w-full rounded-xl bg-brand-600 px-4 py-2.5 text-base font-semibold text-white shadow-lg shadow-brand-600/30 transition hover:bg-brand-700"
              >
                Ir para o login
              </button>
            </div>
          )}

          {info && !sucesso && (
            <>
              <h1 className="text-xl font-bold text-ink">Criar minha conta</h1>
              <p className="mb-6 mt-1 text-sm text-slate-500">
                Cadastro em <span className="font-semibold text-slate-700">{info.predio_nome}</span>
              </p>

              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
                <div>
                  <label className="mb-1 block text-sm font-medium text-slate-700">
                    Nome completo
                  </label>
                  <input
                    className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-base focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
                    {...register("full_name")}
                  />
                  {errors.full_name && (
                    <p className="mt-1 text-sm text-red-600">{errors.full_name.message}</p>
                  )}
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-slate-700">E-mail</label>
                  <input
                    type="email"
                    autoComplete="username"
                    className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-base focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
                    {...register("email")}
                  />
                  {errors.email && <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>}
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-slate-700">Senha</label>
                  <input
                    type="password"
                    autoComplete="new-password"
                    className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-base focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
                    {...register("password")}
                  />
                  {errors.password && (
                    <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
                  )}
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-slate-700">Eu sou</label>
                  <select
                    className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-base focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
                    {...register("role")}
                  >
                    <option value="morador">Morador</option>
                    <option value="proprietario">Proprietario</option>
                  </select>
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-slate-700">
                    Minha(s) unidade(s)
                  </label>
                  <div className="max-h-40 space-y-1 overflow-y-auto rounded-xl border border-slate-300 p-2">
                    {info.unidades.map((u) => (
                      <label
                        key={u.id}
                        className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm hover:bg-slate-50"
                      >
                        <input
                          type="checkbox"
                          checked={(unidadeIdsSelecionadas ?? []).includes(u.id)}
                          onChange={() => toggleUnidade(u.id)}
                          className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-400"
                        />
                        Bloco {u.bloco} - {u.numero}
                      </label>
                    ))}
                    {info.unidades.length === 0 && (
                      <p className="px-2 py-1.5 text-sm text-slate-400">
                        Nenhuma unidade cadastrada neste predio ainda.
                      </p>
                    )}
                  </div>
                  {errors.unidade_ids && (
                    <p className="mt-1 text-sm text-red-600">{errors.unidade_ids.message}</p>
                  )}
                </div>

                {serverError && (
                  <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{serverError}</p>
                )}

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full rounded-xl bg-brand-600 px-4 py-2.5 text-base font-semibold text-white shadow-lg shadow-brand-600/30 transition hover:bg-brand-700 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSubmitting ? "Cadastrando..." : "Criar minha conta"}
                </button>
              </form>
            </>
          )}
        </div>

        <p className="mt-6 text-center text-xs text-slate-400">
          MeuPrédio · gestão de condomínios
        </p>
      </div>
    </div>
  );
}
