import { apiClient } from "./client";
import type { Usuario, UsuarioCreateInput, UsuarioUpdateInput } from "./types";

export async function listUsuarios(): Promise<Usuario[]> {
  const { data } = await apiClient.get<Usuario[]>("/usuarios");
  return data;
}

export async function getUsuario(id: number): Promise<Usuario> {
  const { data } = await apiClient.get<Usuario>(`/usuarios/${id}`);
  return data;
}

export async function createUsuario(input: UsuarioCreateInput): Promise<Usuario> {
  const { data } = await apiClient.post<Usuario>("/usuarios", input);
  return data;
}

export async function updateUsuario(id: number, input: UsuarioUpdateInput): Promise<Usuario> {
  const { data } = await apiClient.patch<Usuario>(`/usuarios/${id}`, input);
  return data;
}

export async function deleteUsuario(id: number): Promise<void> {
  await apiClient.delete(`/usuarios/${id}`);
}

export async function anonimizarUsuario(id: number): Promise<Usuario> {
  const { data } = await apiClient.post<Usuario>(`/usuarios/${id}/anonimizar`);
  return data;
}
