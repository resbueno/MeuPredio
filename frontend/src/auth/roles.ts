import type { RoleEnum, Usuario } from "../api/types";

/** Papel principal OU algum papel adicional (ver Usuario.papeis_extra) -
 * mesma lógica de `roles_efetivos` no backend. Usar em vez de comparar
 * `user.role` direto sempre que a checagem for "este usuário PODE fazer
 * X", nunca quando for "este usuário É especificamente o administrador
 * global" (esse continua exclusivo, só no papel principal). */
export function temPapel(user: Usuario | null | undefined, ...roles: RoleEnum[]): boolean {
  if (!user) return false;
  return roles.includes(user.role) || user.papeis_extra.some((papel) => roles.includes(papel));
}
