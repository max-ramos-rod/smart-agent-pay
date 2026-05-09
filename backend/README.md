# Backend - Smart Agent Pay ⚙️

API responsável por regras de negócio, persistência e execução das estratégias.

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

## 🚀 Melhorias futuras

* Retry de execução
* Logs estruturados
* Monitoramento
* Sistema de filas (Redis/Celery) para múltiplos workers