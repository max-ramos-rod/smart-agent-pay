# Backend - SentinelFi ⚙️

API responsável por regras de negócio, persistência, autenticação por carteira, sessões do agente e execução das estratégias.

---

## 🚀 Stack

* FastAPI
* SQLAlchemy 2
* PostgreSQL
* Pydantic v2
* Alembic

---

## 📁 Estrutura

```
app/
 ├── api/
 ├── core/
 ├── db/
 ├── models/
 ├── schemas/
 ├── services/
```

---

## 🧱 Padrão arquitetural

* Repository Pattern
* Service Layer
* Separation of concerns

---

## 🔁 Fluxo

```
Router → Service → Repository → DB
```

---

## 📦 Models principais

### User

* autenticação
* controle de acesso

### Strategy

* define regras de execução

### Execution

* log de execução das estratégias

### Session

* armazena delegate pubkey e chave efêmera criptografada
* representa a autorização do agente criada on-chain via Anchor

---

## 🔐 Autenticação

* Phantom wallet — challenge/signature (ed25519 via nacl)
* JWT access token (60 min, `type: "access"`) + refresh token (7 dias, `type: "refresh"`)
* `POST /auth/refresh` renova ambos os tokens sem nova assinatura de carteira

---

## ▶️ Rodando o projeto

```bash
# criar venv
python -m venv .venv

# ativar
source .venv/bin/activate  # linux/mac
.venv\Scripts\activate     # windows

# instalar deps
pip install -r requirements.txt

# rodar servidor
uvicorn app.main:app --reload
```

---

## 🧱 Banco de dados

### Rodar migrations

```bash
alembic upgrade head
```

---

## 📡 Endpoints principais

### Auth

```
GET  /auth/challenge
POST /auth/login
POST /auth/refresh
```

---

### Strategies

```
GET    /strategies
POST   /strategies
PATCH  /strategies/{id}
DELETE /strategies/{id}
```

---

### Executions

```
GET  /executions
POST /executions
```

### Sessions

```
POST   /sessions
GET    /sessions
DELETE /sessions
```

### Demo

```
POST   /demo/set-price
DELETE /demo/set-price
GET    /demo/price
```

---

## 📦 Padrão de resposta

```json
{
  "data": ...,
  "meta": {}
}
```

---

## ⚠️ Boas práticas

* Repository não faz commit
* Service controla regras de negócio
* Sempre usar AsyncSession
* Nunca expor password_hash

---

## 🔐 Segurança

* JWT com expiração + refresh token de 7 dias
* CORS restrito via `ALLOWED_ORIGINS` (env var)
* Validação de dados com Pydantic
* Nunca confiar em dados do cliente

---

## Estado atual das Session Keys

* O frontend cria/revoga `SessionToken` no programa Anchor em devnet.
* O backend guarda a chave efêmera criptografada por usuário.
* O worker pode tentar transferências autônomas com essa chave quando há sessão ativa.
* A validação on-chain de limite (`execute_swap` / `amount_spent`) ainda não está integrada ao worker.
* Swaps Jupiter ainda seguem fluxo de assinatura manual via Phantom.

---

## 🚀 Melhorias futuras

* Retry de execução
* Monitoramento
* Sistema de filas (Redis/Celery) para múltiplos workers
* Redis para challenges de auth com TTL
* Integração on-chain de limite de gasto antes de execução autônoma
