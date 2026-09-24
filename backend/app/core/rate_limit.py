"""Lockout de força bruta em memória de processo.

Deliberadamente simples (sem Redis) porque o backend roda como um único
processo uvicorn (ver `Dockerfile`, sem `--workers`) - se isso mudar para
múltiplos workers/réplicas, este estado deixa de ser compartilhado entre
eles e precisa migrar para um backend externo (Redis) para continuar
efetivo. Até lá, thread-safe via lock basta.

Duas chaves independentes por tentativa de login (basta UMA bloquear):
- por conta (e-mail + prédio): impede que um único atacante esgote as
  tentativas de uma conta específica, de qualquer IP.
- por IP: impede que um único IP tente muitas contas em sequência
  (credential stuffing), com limite mais folgado (um IP pode representar
  várias pessoas legítimas atrás de um NAT).
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class _RegraLimite:
    max_tentativas: int
    janela_segundos: float
    bloqueio_segundos: float


_REGRA_CONTA = _RegraLimite(max_tentativas=5, janela_segundos=5 * 60, bloqueio_segundos=15 * 60)
_REGRA_IP = _RegraLimite(max_tentativas=20, janela_segundos=5 * 60, bloqueio_segundos=15 * 60)

_lock = threading.Lock()
_tentativas: dict[str, list[float]] = {}


def _podar(chave: str, agora: float, regra: _RegraLimite) -> list[float]:
    corte = agora - max(regra.janela_segundos, regra.bloqueio_segundos)
    tentativas = [t for t in _tentativas.get(chave, []) if t > corte]
    if tentativas:
        _tentativas[chave] = tentativas
    else:
        _tentativas.pop(chave, None)
    return tentativas


def _segundos_bloqueado(chave: str, regra: _RegraLimite, agora: float) -> float | None:
    tentativas = _podar(chave, agora, regra)
    recentes = [t for t in tentativas if t > agora - regra.janela_segundos]
    if len(recentes) < regra.max_tentativas:
        return None
    restante = regra.bloqueio_segundos - (agora - max(recentes))
    return restante if restante > 0 else None


def segundos_bloqueado_login(email_chave: str, ip: str | None) -> float | None:
    """Maior tempo de bloqueio entre a chave de conta e a de IP, ou None se
    liberado para tentar. `email_chave` já deve incluir o prédio (para não
    misturar contas de mesmo e-mail em prédios diferentes)."""
    agora = time.monotonic()
    with _lock:
        restantes = [_segundos_bloqueado(f"conta:{email_chave}", _REGRA_CONTA, agora)]
        if ip:
            restantes.append(_segundos_bloqueado(f"ip:{ip}", _REGRA_IP, agora))
        restantes = [r for r in restantes if r is not None]
        return max(restantes) if restantes else None


def registrar_falha_login(email_chave: str, ip: str | None) -> None:
    agora = time.monotonic()
    with _lock:
        _tentativas.setdefault(f"conta:{email_chave}", []).append(agora)
        if ip:
            _tentativas.setdefault(f"ip:{ip}", []).append(agora)


def limpar_falhas_login(email_chave: str, ip: str | None) -> None:
    with _lock:
        _tentativas.pop(f"conta:{email_chave}", None)
        if ip:
            _tentativas.pop(f"ip:{ip}", None)
