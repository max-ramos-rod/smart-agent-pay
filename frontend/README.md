# Frontend - Smart Agent Pay 🎨

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

* JWT armazenado no localStorage
* enviado via Authorization header

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

* React hooks
* possível evolução para React Query

---

## 🚀 Melhorias futuras

* Dashboard com métricas
* Gráficos de execução
* Notificações em tempo real
* WebSocket

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