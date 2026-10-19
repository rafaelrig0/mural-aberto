# API do Catálogo de Obras

Backend (FastAPI + PostgreSQL/Supabase) de uma plataforma de divulgação e catalogação de obras
artísticas e literárias. Visitantes enviam obras e comentários sem cadastro; administradores
autenticados moderam tudo.

> O site (público e painel do administrador) está na pasta `../frontend`. Veja o `README.md` dela.

## Stack

| Necessidade | Escolha |
|---|---|
| API | Python 3.12 + FastAPI |
| Banco / ORM / migrações | PostgreSQL (Supabase) + SQLAlchemy 2 (síncrono) + Alembic |
| Validação / config | Pydantic v2 + pydantic-settings |
| Senhas / tokens | argon2 + JWT (PyJWT), enviado em `Authorization: Bearer` |
| Arquivos | Supabase Storage (bucket privado, URLs assinadas), via `httpx` |
| Verificação de uploads | magic bytes (`filetype`) + Pillow |
| Abuso | rate limit por IP (`slowapi`) + limite de tamanho do corpo |
| Qualidade | pytest (Postgres real), ruff, mypy (strict) |

## Estrutura

```
app/
├── main.py              # cria o app: CORS, limite de corpo, handlers, routers
├── models.py            # registro central dos models (importar em qualquer ponto de entrada)
├── core/                # config, database, security, exceptions, rate_limit, pagination, middleware
├── api/                 # deps.py (sessão, admin autenticado) e router.py (agrega os módulos)
├── modules/             # um pacote por assunto de negócio:
│   ├── admins/          #   login, JWT, criação de administradores
│   ├── categories/      #   listagem pública + CRUD administrativo
│   ├── works/           #   envio, catálogo, estados (state.py), moderação, exclusão
│   ├── media/           #   validação de arquivos e StorageService (Supabase)
│   ├── comments/        #   envio público + moderação
│   ├── feedback/        #   opiniões, sugestões e relatos de problemas dos visitantes
│   └── moderation/      #   log de auditoria (append-only) + consulta
└── scripts/             # create_admin, seed_categories, setup_storage
migrations/              # Alembic (0001 = esquema inicial + RLS, 0002 = feedback)
tests/                   # unit/ (regras isoladas) e api/ (fluxos HTTP completos)
```

Em cada módulo: `router.py` (HTTP) → `schemas.py` (contratos) → `service.py` (regras e consultas)
→ `models.py` (tabelas). Não há camada de repositórios: as consultas ficam legíveis nos services.

## Rodando localmente

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env        # preencha DATABASE_URL, JWT_SECRET_KEY e as chaves do Supabase
alembic upgrade head        # cria as tabelas (e liga o RLS)
python -m app.scripts.seed_categories              # categorias iniciais (idempotente)
python -m app.scripts.create_admin --email voce@exemplo.com   # pede a senha no terminal
python -m app.scripts.setup_storage                # cria o bucket privado (ou crie no painel)
uvicorn app.main:app --reload                      # http://localhost:8000/docs
```

Gerar JWT_SECRET_KEY: `python -c "import secrets; print(secrets.token_urlsafe(48))"`.

### Configuração do Supabase

1. **DATABASE_URL:** painel > *Connect* > **Session pooler** (porta 5432). A conexão direta usa IPv6
   e falha em algumas redes e hospedagens. Pode colar a URL `postgresql://…` como está.
2. **SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY:** painel > *Project Settings > API*. A
   `service_role` **nunca** vai para o frontend nem para o Git.
3. **Bucket:** precisa ser **privado**. O script `setup_storage` cria; ou crie no painel.
4. **Limite de arquivo:** o plano gratuito tem um limite global por arquivo (confira no seu projeto,
   *Storage > Settings*). `MAX_VIDEO_SIZE_MB` não deve ultrapassá-lo.
5. **RLS:** a migração liga o Row Level Security em todas as tabelas, sem políticas. Isso bloqueia
   o acesso pela API REST automática do Supabase (chave `anon`). O backend não é afetado porque
   conecta como dono das tabelas (usuário `postgres`).

## Testes e qualidade

Os testes usam **PostgreSQL real** (não SQLite) e recriam/limpam as tabelas a cada execução.

```bash
docker compose up -d test-db     # Postgres de teste em localhost:5433 (banco catalog_test)
pytest
ruff check . && ruff format --check .
mypy app
```

Sem Docker, aponte `TEST_DATABASE_URL` para qualquer banco **cujo nome termine em `_test`**.
Há uma trava: a suíte se recusa a rodar contra outro banco, porque apaga todas as tabelas.
Nenhum teste fala com o Supabase: o Storage é substituído por uma versão em memória.

## Endpoints (`/api/v1`)

**Públicos**

| Método | Rota | Descrição |
|---|---|---|
| GET | `/categories` | Categorias |
| GET | `/works` | Catálogo (só obras aprovadas). Filtros: `category_id`, `work_type`, `q`; paginação `page`, `page_size` |
| GET | `/works/{id}` | Detalhe + comentários aprovados |
| POST | `/works` | Envio de obra (`multipart/form-data`, campos abaixo) |
| POST | `/works/{id}/comments` | Envio de comentário (JSON: `author_name`, `content`) |
| POST | `/feedback` | Envio de feedback sobre o site (JSON, campos abaixo). Responde `201` com `{"id": ...}` |

Campos do `POST /works`: `title`, `author_name`, `contact_email`, `category_id`, `work_type`
(`visual` ou `text`), `created_on` (AAAA-MM-DD), `usage_authorized` (deve ser `true`), opcionais
`neighborhood`, `alt_text`, e conforme o tipo: `body_text` (texto) ou `image` e/ou `video` (visual).
Regras: obra textual exige `body_text` e não aceita arquivos; obra visual exige ao menos um arquivo
e não aceita `body_text`; imagem exige `alt_text`. No máximo 1 imagem e 1 vídeo por obra.
Imagens: JPEG, PNG, WebP. Vídeos: MP4, WebM.

Campos do `POST /feedback`: `feedback_type` (obrigatório: `opinion`, `suggestion`, `bug` ou `other`),
`message` (obrigatório, 5 a 2000 caracteres), `author_name` (opcional, até 120) e `rating`
(opcional, inteiro de 1 a 5). Campos inválidos respondem `422` com `error.details` indicando o campo.

**Administrativos** (exigem `Authorization: Bearer <token>`)

| Método | Rota | Descrição |
|---|---|---|
| POST | `/auth/login` | Devolve o token (público, com rate limit) |
| GET | `/auth/me` | Admin autenticado |
| GET | `/admin/works` | Lista por `status` (`pending`, `approved`, `rejected`, `archived`), `order` (`newest`/`oldest`) |
| GET | `/admin/works/{id}` | Detalhe completo (inclui `contact_email`) |
| POST | `/admin/works/{id}/approve` · `/archive` · `/unarchive` | Moderação |
| POST | `/admin/works/{id}/reject` | Corpo `{"reason": "..."}` (obrigatório) |
| DELETE | `/admin/works/{id}` | Exclusão definitiva (remove arquivos e comentários; o log permanece) |
| GET | `/admin/comments` | Lista por `status`, `work_id` |
| POST | `/admin/comments/{id}/approve` · `/reject` | `reject` aceita `{"reason": "..."}` opcional |
| DELETE | `/admin/comments/{id}` | Exclusão definitiva |
| POST/PUT/DELETE | `/admin/categories[/{id}]` | CRUD (não exclui categoria com obras) |
| GET | `/admin/feedback` | Lista os feedbacks recebidos. Filtro: `feedback_type`; `order` (`newest`/`oldest`); paginação |
| GET | `/admin/moderation-logs` | Histórico. Filtros: `target_type`, `target_id`, `admin_id`, `action` |

Erros seguem sempre `{"error": {"code": "...", "message": "...", "details": [...]}}`.

## Regras de negócio

- Obra e comentário nascem `pending` e só aparecem ao público depois de `approved`.
- Obra: `pending → approved | rejected`, `approved → archived`, `archived → approved`.
  **Rejeitada é estado final.** Comentário: `pending → approved | rejected`.
- Rejeitar obra exige motivo; rejeitar comentário aceita motivo opcional.
- Mudança de estado e registro de moderação são gravados **na mesma transação**, com a linha da
  obra travada (`SELECT … FOR UPDATE`): dois admins agindo ao mesmo tempo são serializados.
- Só obras aprovadas aceitam comentários. Obra não aprovada responde 404 ao público.
- O log de moderação guarda só `target_type` + `target_id` (sem chave estrangeira): sobrevive à
  exclusão definitiva sem manter dados pessoais. Não escreva dados pessoais nos motivos.
- A autorização de uso é registrada em `usage_authorized_at`.

## Segurança: o que foi feito

- Senhas com argon2; login com mensagem genérica e tempo de resposta igualado (não revela e-mails).
- JWT curto (`JWT_EXPIRE_MINUTES`); a cada requisição o admin é relido do banco, então desativar
  uma conta (`is_active = false`) revoga o acesso na hora.
- Uploads: limite de tamanho, tipo **real** pelos primeiros bytes (extensão e `Content-Type` do
  cliente são ignorados), imagem decodificada com Pillow e limite de pixels, nome gerado por UUID.
- Limite do corpo da requisição: imagem + vídeo + 1 MB no envio de obras (61 MB com os padrões); 1 MB nas demais rotas.
- Se o banco falhar após o upload, os arquivos enviados são apagados (compensação).
- `contact_email`, `storage_path` e motivos de rejeição existem só nos schemas administrativos.
- CORS restrito a `CORS_ORIGINS` (em produção a aplicação **não inicia** com lista vazia ou `*`).
- Rate limit por IP: login, envio de obra, de comentário e de feedback (configurável por variável).
- Erros 500 não expõem detalhes; `/docs` e `/openapi.json` ficam desligados em produção.
- Segredos só em variáveis de ambiente (`SecretStr`, nunca aparecem em logs).

## Deploy (Render)

- **Build:** `pip install -r requirements.txt`
- **Start:** `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'`
- **Variáveis:** as do `.env.example`, com `ENVIRONMENT=production`, `CORS_ORIGINS` com a URL
  real do frontend e `PYTHON_VERSION=3.12`.
- `--proxy-headers` é necessário para o rate limit enxergar o IP real do visitante, e não o do
  proxy. `--forwarded-allow-ips='*'` é aceitável no Render porque só o proxy deles alcança o contêiner.
- Rode `create_admin` e `seed_categories` uma vez apontando `DATABASE_URL` para o Supabase
  (do seu computador ou pelo shell do Render).
- **Use 1 worker.** O contador do rate limit fica na memória do processo.
- No plano gratuito o serviço "adormece" por inatividade: a primeira requisição demora.

## Limitações conhecidas

- **Integração com o Supabase Storage não foi exercitada contra um projeto real.** Os testes
  verificam o formato das chamadas com transporte simulado, seguindo a API REST documentada.
  Faça um envio de obra com imagem de ponta a ponta no seu ambiente antes de entregar.
- O arquivo inteiro é lido para a memória (até 60 MB por envio com os limites padrão). Em
  hospedagem com pouca RAM, reduza `MAX_VIDEO_SIZE_MB`.
- Não há CAPTCHA (decisão do MVP): o único freio a envios anônimos é o rate limit por IP.
- Redes compartilhadas (escola, empresa) dividem o mesmo IP e, portanto, o mesmo limite.
- Fora do MVP: e-mail de notificação de rejeição, CI/CD, Docker de produção, monitoramento.
- Texto de comentários e obras é guardado como foi enviado; o **frontend deve escapá-lo** ao exibir.
- Rotas de listagem do admin não têm busca textual.
- Feedback não passa por moderação: fica salvo como foi enviado e só o admin o vê. Como todo texto
  livre, **o frontend deve escapá-lo** ao exibir (a API devolve o texto sem alterar).
