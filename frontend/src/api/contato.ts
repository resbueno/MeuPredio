import { apiClient } from "./client";
import type { ContatoLeadCreateInput } from "./types";

export async function enviarContato(input: ContatoLeadCreateInput): Promise<void> {
  await apiClient.post("/contato", input);
}
