# Royal Advice: frontend da Taverna da Bruxa

Fluxo: porta da taverna → a bruxa pede a tag → "adivinha" o jogador (deck + coleção) →
o jogador escolhe uma poção (Análise, Dicas, Trocas sugeridas, Resumo) → a bruxa sobe e a
câmera mergulha no caldeirão, onde dá para conversar com a LLM.

## Rodando localmente

```bash
npm install
npm run dev
```

`VITE_API_URL` (`.env`) define a base do backend - `http://localhost:8000` em dev,
já que o backend (FastAPI) roda numa porta separada da do Vite.

## Contrato do backend (implementado em `app/routers/frontend_api.py`)

### `GET /api/players/:tag`  (tag sem `#`)
Proxy da API oficial `GET /v1/players/%23{tag}`. Devolve o JSON como vem
(`currentDeck`, `cards` com `iconUrls.medium` / `evolutionMedium`, etc.). 404 quando não existir.

### `POST /api/witch/chat`
```json
{
  "mode": "analise | dicas | trocas | resumo",
  "messages": [{ "role": "user", "content": "..." }],
  "player": { "name": "...", "trophies": 0, "avgElixir": 3.1, "deck": [...], "topCards": [...] }
}
```
O front aceita qualquer um destes formatos, mas o backend atual sempre devolve
`application/json` com `{ "reply": "..." }` - a animação de digitação é só
client-side (`useTypewriter`), então streaming real do backend não é necessário.

Markdown simples (títulos `##`, listas, `**negrito**`) é renderizado no balão.
O backend usa os modelos configurados em `OPENROUTER_PRIMARY_MODEL`/`_FALLBACK_MODEL`
(veja `.env.example` na raiz do projeto) e rejeita respostas que parecem
racionínio vazado em inglês, tentando o modelo de fallback automaticamente
(veja `_reject_leaked_reasoning` em `frontend_api.py`).

## Níveis das cartas
A API devolve nível relativo à raridade. O front normaliza usando o maior `maxLevel`
da coleção (o das comuns), então não há número mágico para atualizar quando o jogo subir o teto.
