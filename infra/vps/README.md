# Deploy do MeuPredio na VPS de homologação compartilhada (SIGA)

Este diretório é específico para conviver na mesma VPS de homologação onde o
SIGA já roda (`ssh siga-homolog`, 162.35.175.50). **Não confundir com o
`docker-compose.yml` da raiz do repo**, que é para dev local isolado.

## Por que é diferente do compose local

Inspeção da VPS (ver histórico da sessão) mostrou que:

- Só `gateway_nginx` publica porta no host (80/443). Todo o resto do SIGA
  fica só na rede Docker interna `siga_siga_net`.
- Não há firewall (`ufw` inativo) — qualquer porta publicada no host fica
  exposta à internet sem TLS.
- RAM é escassa (3.3GB no total, uso real baixo mas `mem_limit` já reservam
  boa parte como teto).
- O próprio `~/gateway/docker-compose.yml` documenta a convenção: novos
  projetos entram no gateway (rede + `location` dedicado), não publicando
  porta própria.

Por isso este compose:
- não publica nenhuma porta;
- entra na rede externa `siga_siga_net`;
- define `mem_limit`/`cpus` por serviço;
- serve o frontend como build estático via nginx (não o dev server do Vite).

## Passo a passo

1. **Copiar o projeto para a VPS** (fora do `~/siga`, para não ser
   gerenciado pelo compose deles):
   ```bash
   rsync -az --exclude node_modules --exclude .git --exclude frontend/dist \
     ./ siga-homolog:~/meupredio/
   ```

2. **Configurar segredos** na VPS:
   ```bash
   ssh siga-homolog 'cp ~/meupredio/infra/vps/.env.example ~/meupredio/infra/vps/.env'
   # editar ~/meupredio/infra/vps/.env na VPS: SECRET_KEY, POSTGRES_PASSWORD, FIRST_ADMIN_*
   ```

3. **Build sequencial** (não `docker compose build` paralelo, para não
   espichar memória com dois builds Node/Python ao mesmo tempo):
   ```bash
   ssh siga-homolog 'cd ~/meupredio/infra/vps && docker compose build backend'
   ssh siga-homolog 'free -h'   # conferir sobra de memória entre builds
   ssh siga-homolog 'cd ~/meupredio/infra/vps && docker compose build nginx'
   ```

4. **Subir a stack**, banco primeiro:
   ```bash
   ssh siga-homolog 'cd ~/meupredio/infra/vps && docker compose up -d db'
   ssh siga-homolog 'cd ~/meupredio/infra/vps && docker compose up -d backend'
   ssh siga-homolog 'docker logs meupredio_backend --tail 50'   # confirmar migration + seed_admin ok
   ssh siga-homolog 'cd ~/meupredio/infra/vps && docker compose up -d nginx'
   ```

5. **Adicionar a rota no gateway compartilhado** (`gateway-location-snippet.conf`
   neste diretório) dentro de `~/gateway/nginx.conf`, **com backup antes**:
   ```bash
   ssh siga-homolog 'cp ~/gateway/nginx.conf ~/gateway/nginx.conf.bak-$(date +%s)'
   # inserir o bloco de gateway-location-snippet.conf no server{} HTTPS
   ssh siga-homolog 'docker exec gateway_nginx nginx -t'      # validar sintaxe
   ssh siga-homolog 'docker exec gateway_nginx nginx -s reload'
   ```

6. **Smoke test** (MeuPredio novo e SIGA continuando de pé):
   ```bash
   ssh siga-homolog 'curl -sk -o /dev/null -w "%{http_code}\n" https://127.0.0.1/meupredio/health'
   ssh siga-homolog 'curl -sk -o /dev/null -w "%{http_code}\n" https://127.0.0.1/iacto/'
   ssh siga-homolog 'docker ps --format "{{.Names}}: {{.Status}}"'
   ssh siga-homolog 'free -h'
   ```

## Rollback

```bash
ssh siga-homolog 'cd ~/meupredio/infra/vps && docker compose down'
ssh siga-homolog 'cp ~/gateway/nginx.conf.bak-<timestamp> ~/gateway/nginx.conf'
ssh siga-homolog 'docker exec gateway_nginx nginx -s reload'
```

Isso não toca em nenhum container/arquivo do SIGA — só remove o que o
MeuPredio acrescentou.
