import { apiClient } from "./client";

export async function baixarDocumento(documentoUrl: string): Promise<string> {
  const { data } = await apiClient.get(documentoUrl, { responseType: "blob" });
  return URL.createObjectURL(data as Blob);
}
