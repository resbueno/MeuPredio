"""Configuração da aplicação via variáveis de ambiente (pydantic-settings).

Todos os valores sensíveis (senhas, chave JWT) vêm exclusivamente de variáveis
de ambiente / arquivo `.env` — nunca ficam hardcoded no código-fonte. Veja
`.env.example` na raiz do repositório para a lista completa de variáveis.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Procura um .env tanto na pasta backend/ (dev local sem Docker)
        # quanto na raiz do repositório (quando executado a partir dela).
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Aplicação ---
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "MeuPredio API"
    API_V1_PREFIX: str = ""

    # --- Banco de dados ---
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://meupredio:meupredio@localhost:5432/meupredio",
        description="String de conexão SQLAlchemy do banco principal.",
    )
    DATABASE_URL_TEST: str | None = Field(
        default=None,
        description="String de conexão do banco usado pela suíte de testes.",
    )

    # --- Segurança / JWT ---
    # SEM valor default de produção: se SECRET_KEY não for definido via env/.env,
    # a aplicação falha explicitamente ao subir (ver validador abaixo) em vez de
    # usar um segredo previsível.
    SECRET_KEY: str = Field(default="", description="Chave de assinatura dos JWTs.")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- CORS ---
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- Bootstrap do primeiro administrador (seed_admin.py) ---
    FIRST_ADMIN_EMAIL: str | None = None
    FIRST_ADMIN_PASSWORD: str | None = None
    FIRST_ADMIN_FULL_NAME: str = "Administrador"

    # A validação de que SECRET_KEY foi de fato configurada (fora de testes)
    # acontece em get_settings() abaixo, não aqui — precisa rodar depois que
    # o valor é carregado do ambiente, e deve ser pulada quando
    # ENVIRONMENT=test (conftest.py injeta uma SECRET_KEY dedicada de teste).

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def sqlalchemy_database_url_test(self) -> str:
        return self.DATABASE_URL_TEST or self.DATABASE_URL.rstrip("/") + "_test"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.ENVIRONMENT != "test" and not settings.SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY não está definida. Configure a variável de ambiente "
            "SECRET_KEY (veja .env.example) antes de iniciar a aplicação."
        )
    return settings
