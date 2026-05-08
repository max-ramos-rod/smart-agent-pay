# Smart Agent Pay 🚀

Sistema de automação de estratégias financeiras com execução baseada em condições de mercado.

## 🧠 Visão Geral

O sistema permite que usuários:

* Criem estratégias automatizadas
* Monitorem preços de ativos (ex: SOL)
* Executem ações automaticamente (compra)
* Registrem execuções (logs/auditoria)

---

## 🧱 Arquitetura

```text
Frontend (React)
        ↓
Backend API (FastAPI)
        ↓
Banco de Dados (PostgreSQL)
```

---

## 🔑 Conceitos principais

### Strategy

Define a regra de execução:

* percentual de queda
* valor a investir
* preço de referência

---

### Execution

Registro de cada execução da estratégia:

* status (pending, confirmed, failed)
* tx_hash
* explicação
* auditoria completa

---

### Wallet

Representa a identidade do usuário na blockchain e executa transações.

---

## 📁 Estrutura

```
backend/
frontend/
```

---

## 🚀 Tecnologias

### Backend

* FastAPI
* SQLAlchemy 2
* PostgreSQL
* Pydantic v2

### Frontend

* React + TypeScript
* Axios
* React Query

---

## 🔐 Autenticação

* JWT
* OAuth2PasswordRequestForm

---

## ⚠️ Observações

* Backend é a fonte de verdade
* Frontend não acessa banco diretamente
* Todas as respostas seguem padrão envelope `{ data, meta }`

---

## 🚀 Roadmap

* [ ] Execução automática (worker)
* [ ] Integração com preço em tempo real
* [ ] Refresh token
* [ ] RBAC (roles/permissões)
* [ ] Sistema de filas (Redis/Celery)

---

## 👨‍💻 Autor

PETECO HACKTHON