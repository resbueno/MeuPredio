#!/usr/bin/env bash
# Executado automaticamente pela imagem postgres:16-alpine na PRIMEIRA
# inicialização do volume de dados (diretório /docker-entrypoint-initdb.d).
# Cria o banco de dados separado usado pela suíte de testes do backend,
# além do banco principal (já criado pela variável POSTGRES_DB).
set -euo pipefail

TEST_DB="${POSTGRES_DB_TEST:-meupredio_test}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    SELECT 'CREATE DATABASE "${TEST_DB}"'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${TEST_DB}')\gexec
EOSQL

echo "Banco de teste '${TEST_DB}' verificado/criado com sucesso."
