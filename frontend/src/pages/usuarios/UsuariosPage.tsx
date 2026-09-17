import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { AppShell } from "../../components/layout/AppShell";
import { useAuth } from "../../auth/AuthContext";
import {
  anonimizarUsuario,
  createUsuario,
  deleteUsuario,
  listUsuarios,
  updateUsuario,
} from "../../api/usuarios";
import type { RoleEnum, Usuario, UsuarioCreateInput, UsuarioUpdateInput } from "../../api/types";

const ROLES: RoleEnum[] = ["morador", "proprietario", "sindico", "zelador", "administrador"];

const ROLE_LABELS: Record<RoleEnum, string> = {
  morador: "Morador",
  proprietario: "Proprietario",
  sindico: "Sindico",
  zelador: "Zelador",
  administrador: "Administrador",
};

function parseUnidadeIds(texto: string | undefined): number[] {
  return (texto ?? "")
    .split(",")
    .map((parte) => parte.trim())
    .filter(Boolean)
    .map(Number)
    .filter((n) => !Number.isNaN(n));
}

const usuarioSchema = z.object({
  email: z.string().min(1, "Informe o e-mail.").email("Informe um e-mail valido."),
  full_name: z.string().min(2, "Informe o nome completo."),
  role: z.enum(["morador", "proprietario", "sindico", "zelador", "administrador"]),
  unidade_ids: z.string().optional(),
  predio_id: z.string().optional(),
  password: z.string().optional(),
});

type UsuarioFormValues = z.infer<typeof usuarioSchema>;

export function UsuariosPage() {
  const { user: currentUser } = useAuth();
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<Usuario | null>(null);
  const souAdministrador = currentUser?.role === "administrador";

  const { data: usuarios, isLoading } = useQuery({
    queryKey: ["usuarios"],
    queryFn: listUsuarios,
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<UsuarioFormValues>({
    resolver: zodResolver(usuarioSchema),
    defaultValues: {
      email: "",
      full_name: "",
      role: "morador",
      unidade_ids: "",
      predio_id: "",
      password: "",
    },
  });

  useEffect(() => {
    if (editing) {
      reset({
        email: editing.email,
        full_name: editing.full_name,
        role: editing.role,
        unidade_ids: editing.unidade_ids.join(", "),
        predio_id: editing.predio_id ? String(editing.predio_id) : "",
        password: "",
      });
    } else {
      reset({ email: "", full_name: "", role: "morador", unidade_ids: "", predio_id: "", password: "" });
    }
  }, [editing, reset]);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["usuarios"] });

  const createMutation = useMutation({
    mutationFn: createUsuario,
    onSuccess: () => {
      invalidate();
      reset({ email: "", full_name: "", role: "morador", unidade_ids: "", predio_id: "", password: "" });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: number; input: UsuarioUpdateInput }) =>
      updateUsuario(id, input),
    onSuccess: () => {
      invalidate();
      setEditing(null);
    },
  });

  const deleteMutation = useMutation({ mutationFn: deleteUsuario, onSuccess: invalidate });
  const anonimizarMutation = useMutation({ mutationFn: anonimizarUsuario, onSuccess: invalidate });

  function onSubmit(values: UsuarioFormValues): void {
    const unidadeIds = parseUnidadeIds(values.unidade_ids);
    const predioId = values.predio_id?.trim();

    if (editing) {
      const input: UsuarioUpdateInput = {
        full_name: values.full_name,
        role: values.role,
        unidade_ids: values.role === "administrador" ? [] : unidadeIds,
      };
      if (values.password) {
        input.password = values.password;
      }
      updateMutation.mutate({ id: editing.id, input });
      return;
    }

    if (!values.password || values.password.length < 8) {
      return;
    }
    const input: UsuarioCreateInput = {
      email: values.email,
      full_name: values.full_name,
      role: values.role,
      unidade_ids: values.role === "administrador" ? [] : unidadeIds,
      predio_id: predioId ? Number(predioId) : undefined,
      password: values.password,
    };
    createMutation.mutate(input);
  }

  const erroMutacao = createMutation.error ?? updateMutation.error;

  return (
    <AppShell>
      <h1 className="mb-4 text-xl font-bold text-slate-800">Usuarios</h1>

      <form
        onSubmit={handleSubmit(onSubmit)}
        className="mb-6 space-y-3 rounded-2xl bg-white p-4 shadow-sm"
        noValidate
      >
        <h2 className="text-sm font-semibold text-slate-700">
          {editing ? `Editar usuario #${editing.id}` : "Novo usuario"}
        </h2>

        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">E-mail</label>
          <input
            type="email"
            disabled={Boolean(editing)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-100"
            {...register("email")}
          />
          {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>}
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">Nome completo</label>
          <input
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            {...register("full_name")}
          />
          {errors.full_name && (
            <p className="mt-1 text-xs text-red-600">{errors.full_name.message}</p>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Papel</label>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              {...register("role")}
            >
              {ROLES.filter((role) => role !== "administrador" || souAdministrador).map((role) => (
                <option key={role} value={role}>
                  {ROLE_LABELS[role]}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">
              ID(s) da(s) unidade(s)
            </label>
            <input
              placeholder="Ex.: 12, 13"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              {...register("unidade_ids")}
            />
          </div>
        </div>

        {souAdministrador && !editing && (
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">
              ID do predio (obrigatorio quando o papel nao e administrador)
            </label>
            <input
              inputMode="numeric"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              {...register("predio_id")}
            />
          </div>
        )}

        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">
            {editing ? "Nova senha (opcional)" : "Senha"}
          </label>
          <input
            type="password"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            {...register("password")}
          />
          <p className="mt-1 text-xs text-slate-400">Minimo 8 caracteres, com letras e numeros.</p>
        </div>

        {erroMutacao && (
          <p className="text-sm text-red-600">
            Nao foi possivel salvar o usuario. Verifique os dados e tente novamente.
          </p>
        )}

        <div className="flex gap-2">
          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {editing ? "Salvar" : "Adicionar"}
          </button>
          {editing && (
            <button
              type="button"
              onClick={() => setEditing(null)}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600"
            >
              Cancelar
            </button>
          )}
        </div>
      </form>

      {isLoading && <p className="text-sm text-slate-500">Carregando...</p>}

      <ul className="space-y-2">
        {usuarios?.map((usuario) => (
          <li key={usuario.id} className="rounded-xl bg-white p-3 shadow-sm">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="truncate font-medium text-slate-800">{usuario.full_name}</p>
                <p className="truncate text-xs text-slate-500">{usuario.email}</p>
                <p className="mt-0.5 text-xs text-slate-500">
                  {ROLE_LABELS[usuario.role]}
                  {!usuario.is_active && " - inativo"}
                </p>
              </div>
              <div className="flex shrink-0 flex-col items-end gap-1">
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => setEditing(usuario)}
                    className="text-xs font-medium text-brand-600"
                  >
                    Editar
                  </button>
                  <button
                    type="button"
                    onClick={() => deleteMutation.mutate(usuario.id)}
                    className="text-xs font-medium text-red-600"
                  >
                    Remover
                  </button>
                </div>
                {souAdministrador && !usuario.anonymized_at && (
                  <button
                    type="button"
                    onClick={() => {
                      if (
                        window.confirm(
                          "Anonimizar este usuario e irreversivel e remove seus dados pessoais. Continuar?"
                        )
                      ) {
                        anonimizarMutation.mutate(usuario.id);
                      }
                    }}
                    className="text-xs font-medium text-amber-600"
                  >
                    Anonimizar (LGPD)
                  </button>
                )}
              </div>
            </div>
          </li>
        ))}
        {usuarios?.length === 0 && (
          <li className="rounded-xl bg-white p-4 text-center text-sm text-slate-500 shadow-sm">
            Nenhum usuario cadastrado.
          </li>
        )}
      </ul>
    </AppShell>
  );
}
