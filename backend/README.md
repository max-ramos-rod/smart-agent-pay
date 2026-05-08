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

* JWT
* OAuth2PasswordBearer

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
POST /auth/login
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

* JWT com expiração
* validação de dados com Pydantic
* nunca confiar em dados do cliente

---

## 🚀 Melhorias futuras

* Worker assíncrono
* Retry de execução
* Logs estruturados
* Monitoramento