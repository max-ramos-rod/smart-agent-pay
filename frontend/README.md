# Frontend - SentinelFi 🎨

Interface do usuário para criação e monitoramento de estratégias.

---

## 🚀 Stack

* React
* TypeScript
* Axios
* React Query

---

## 📁 Estrutura

```
src/
 ├── pages/
 ├── services/
 ├── types/
 ├── hooks/
```

---

## 🔁 Comunicação com API

Todos os requests passam pelo client Axios:

```ts
api.get<T>()
api.post<T>()
```

---

## 📦 Padrão de resposta

Backend retorna:

```json
{
  "data": [...],
  "meta": {}
}
```

O client já retorna apenas `data`.

---

## ▶️ Rodando o projeto

```bash
npm install
npm run dev
```

---

## 🔐 Autenticação

* Phantom wallet — assinatura de challenge (ed25519)
* Access token (JWT, 60 min) + refresh token (7 dias) no localStorage
* Interceptor Axios renova o token silenciosamente via `/auth/refresh` em caso de 401

---

## 📊 Funcionalidades

* Criar estratégia
* Listar estratégias
* Executar estratégia
* Visualizar execuções

---

## ⚠️ Regras importantes

* Nunca acessar banco diretamente
* Sempre usar backend
* Não confiar em dados locais

---

## 🧠 Estado

* React Query (@tanstack/react-query) para server state
* React hooks para estado local

---

## 🚀 Melhorias futuras

* Dashboard com métricas
* Notificações em tempo real (WebSocket)
* Feed de atividades do agente humanizado

---

## 🔐 Segurança

* Nunca armazenar dados sensíveis
* validação no frontend é apenas UX (backend valida tudo)

---

## 💡 Dica

Sempre tipar as respostas da API:

```ts
api.get<Strategy[]>("/strategies")
```