/**
 * Decodifica (sem validar assinatura) o payload de um JWT.
 *
 * Usado apenas para conveniências de UI (ex.: extrair o id do usuário logado
 * para buscar seu perfil completo). A validação de fato acontece sempre no
 * backend — o frontend nunca deve tomar decisões de autorização confiando
 * cegamente neste payload.
 */
export function decodeJwtPayload<T = Record<string, unknown>>(token: string): T | null {
  try {
    const payloadPart = token.split(".")[1];
    if (!payloadPart) return null;
    const normalized = payloadPart.replace(/-/g, "+").replace(/_/g, "/");
    const padLength = (4 - (normalized.length % 4)) % 4;
    const padded = normalized + "=".repeat(padLength);
    const json = decodeURIComponent(
      atob(padded)
        .split("")
        .map((c) => "%" + c.charCodeAt(0).toString(16).padStart(2, "0"))
        .join("")
    );
    return JSON.parse(json) as T;
  } catch {
    return null;
  }
}
