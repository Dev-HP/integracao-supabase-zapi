# Supabase + Z-API · Desafio b2bflow

Script em Python que lê contatos cadastrados no **Supabase** e envia, via **Z-API**, a mensagem personalizada:

> Olá, {nome} tudo bem com você?

Envia para até **3 números** (ou menos, se houver menos contatos no banco).

---

## Arquitetura e Boas Práticas

Este projeto foi desenvolvido seguindo os princípios **SOLID**, especialmente:

### D — Dependency Inversion Principle

A lógica de negócio **não conhece** a Z-API diretamente. Ela depende de uma interface abstrata `MessagingService`:

```
main.py
       │
       ▼
MessagingService   ←── interface abstrata (src/messaging_service.py)
       │
       ▼
ZApiMessagingService  ←── implementação concreta (src/zapi_service.py)
```

**Benefício:** Para trocar a Z-API por Twilio, WhatsApp Cloud API ou qualquer outro provedor, basta criar uma nova classe que implemente `MessagingService` — sem tocar no `main.py`.

### Outras boas práticas aplicadas:

| Prática | Onde |
|---|---|
| **Single Responsibility** | Cada módulo tem uma única responsabilidade |
| **Separation of Concerns** | Config, logs, dados e mensageria isolados |
| **Retry + Backoff Exponencial** | Resiliência a falhas temporárias de rede |
| **Type Hints** | Tipagem forte em todo o código |
| **Dataclasses** | Estruturas de dados imutáveis e type-safe |
| **Environment Variables** | Credenciais isoladas do código via `.env` |
| **Logs Estruturados** | Rastreabilidade completa do fluxo |
| **Validação de Telefone** | Normalização automática dos números |

---

## Requisitos

- Python 3.14+ (gerenciado via [pyenv](https://github.com/pyenv-win/pyenv-win))
- Conta no [Supabase](https://supabase.com/) (plano gratuito) **ou** Docker para self-hosting
- Conta na [Z-API](https://z-api.io/) com WhatsApp conectado (plano gratuito)

---

## Setup do Ambiente Python com pyenv

O arquivo `.python-version` na raiz do projeto define automaticamente a versão correta.

```bash
# 1. Instalar pyenv-win (Windows)
pip install pyenv-win --target "$HOME\.pyenv"

# 2. Instalar a versão correta do Python
pyenv install 3.14.2

# 3. Criar e ativar ambiente virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

# 4. Instalar dependências
pip install -r requirements.txt

# (opcional) dependências de desenvolvimento
pip install -r requirements-dev.txt
```

---

## Setup da Tabela no Supabase

### Opção 1: Supabase Cloud (plano gratuito)

No **SQL Editor** do painel Supabase, execute:

```sql
create table if not exists contatos (
  id bigint generated always as identity primary key,
  nome text not null,
  telefone text not null,
  status_envio text default 'pendente' check (status_envio in ('pendente', 'enviado', 'erro')),
  enviado_em timestamptz,
  erro_msg text,
  created_at timestamptz default now()
);

alter table contatos enable row level security;

-- Remove a política se existir (Idempotência no script)
drop policy if exists "Leitura pública de contatos" on contatos;

create policy "Leitura pública de contatos"
  on contatos for all
  using (true);

insert into contatos (nome, telefone, status_envio) values
  ('Maria Silva', '5511999999999', 'pendente'),
  ('João Santos',  '5511888888888', 'pendente'),
  ('Ana Costa',   '5511777777777', 'pendente');

### Opção 2: Self-Hosting com Docker *(Diferencial Técnico)*

Execute o Supabase **100% local**, sem dependência de nuvem:

```bash
docker-compose up -d
```

Aguarde ~30 segundos e acesse:

| Serviço | URL |
|---|---|
| **Studio** (interface admin) | http://localhost:3000 |
| **API REST** | http://localhost:8000 |

Configure o `.env` para apontar para o servidor local:

```env
SUPABASE_URL=http://localhost:8000
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlhdCI6MTYxMzUzMTk4NSwiZXhwIjoxOTI5MTA3OTg1fQ.ReEThKB9sHKJOoSgIVpRrmMkUNrGkrEO8aKWLimhvMo
```

> A migração `supabase/migrations/001_create_contatos.sql` é executada automaticamente pelo Docker na primeira inicialização.

---

## Variáveis de Ambiente

Copie o arquivo de exemplo e preencha com suas credenciais:

```bash
cp .env.example .env
```

| Variável | Descrição |
|---|---|
| `SUPABASE_URL` | URL do projeto (Settings → API) |
| `SUPABASE_KEY` | Chave `anon` ou `service_role` |
| `ZAPI_INSTANCE_ID` | ID da instância Z-API |
| `ZAPI_TOKEN` | Token da instância Z-API |
| `ZAPI_CLIENT_TOKEN` | Client-Token (aba Segurança no painel Z-API) |
| `MAX_CONTACTS` | Máximo de contatos a enviar (padrão: `3`) |
| `LOG_LEVEL` | Nível de log: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

---

## Como Rodar

```bash
# Executar o sistema principal
python main.py
```

---

## Estrutura do Projeto

```
.
├── main.py                         # Ponto de entrada
├── src/
│   ├── config.py                   # Carregamento de configurações (.env)
│   ├── logger.py                   # Setup de logs estruturados
│   ├── supabase_client.py          # Repositório de contatos (Supabase)
│   ├── messaging_service.py        # Interface abstrata (Dependency Inversion)
│   └── zapi_service.py             # Implementação concreta Z-API
├── supabase/
│   └── migrations/
│       └── 001_create_contatos.sql # Migração inicial (self-hosting)
├── docker-compose.yml              # Supabase self-hosted (diferencial)
├── requirements.txt                # Dependências de produção (versões fixadas)
├── requirements-dev.txt            # Dependências de desenvolvimento
├── .python-version                 # Versão Python para pyenv (3.14.2)
├── .env.example                    # Template de variáveis de ambiente
└── README.md
```

---

## Diferenciais Técnicos

1. **Dependency Inversion (SOLID-D):** Provedor de WhatsApp é plugável — trocar Z-API por Twilio é criar uma classe
2. **Supabase Self-Hosting:** Docker Compose para rodar 100% local/on-premise, sem conta na nuvem
3. **Retry com Backoff Exponencial:** Resiliência automática a falhas temporárias
4. **pyenv + `.python-version`:** Versão Python reproduzível em qualquer máquina
5. **requirements separados:** `requirements.txt` (prod) vs `requirements-dev.txt` (dev)
6. **Conventional Commits:** Histórico Git legível e padronizado (ver seção abaixo)
7. **Validação de Telefone:** Normalização automática antes do envio
8. **Logs Estruturados:** Rastreabilidade completa com nível configurável

---

## Conventional Commits

Este projeto segue o padrão **[Conventional Commits](https://www.conventionalcommits.org/)** para manter o histórico Git limpo e legível:

### Formato

```
<tipo>(<escopo>): <descrição curta>

[corpo opcional]

[rodapé opcional]
```

### Tipos

| Tipo | Quando usar |
|---|---|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `docs` | Documentação |
| `refactor` | Refatoração sem mudar comportamento |
| `test` | Testes |
| `chore` | Tarefas de manutenção (deps, config) |
| `ci` | Integração contínua |

### Exemplos usados neste projeto

```bash
feat(supabase): adiciona repositório de contatos com tipagem forte
feat(zapi): implementa serviço de mensageria com retry exponencial
feat(solid): extrai interface MessagingService (Dependency Inversion)
refactor(config): centraliza carregamento de variáveis de ambiente
docs(readme): adiciona seção de self-hosting com Docker
chore(deps): fixa versões no requirements.txt e cria requirements-dev.txt
chore(pyenv): adiciona .python-version para reproducibilidade do ambiente
feat(docker): adiciona docker-compose para Supabase self-hosted
```

---

## Fluxo de Execução

```
main.py
    │
    ├── 1. load_settings()           # Carrega e valida .env
    ├── 2. SupabaseContactRepository # Conecta ao Supabase
    ├── 3. fetch_contacts(limit=3)   # Busca apenas contatos com status='pendente'
    ├── 4. ZApiMessagingService      # Instancia provedor de mensagens
    └── 5. Para cada contato:
            ├── build_message(nome)  # "Olá, {nome} tudo bem com você?"
            ├── send_text_message()  # Envia via Z-API (com retry para 5xx)
            └── mark_sent()          # Atualiza status no banco ('enviado' ou 'erro')
