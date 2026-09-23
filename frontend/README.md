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

## Deploy no Vercel

1. **Fazer build local:**
   ```bash
   npm run build
   ```
   Gera `dist/` com o app estático pronto.

2. **Conectar o repo ao Vercel:**
   ```bash
   npx vercel
   ```
   Ou via Dashboard: https://vercel.com/dashboard — conectar seu GitHub repo.

3. **Configurar a variável de ambiente:**
   - No Vercel Dashboard, vá para **Settings → Environment Variables**
   - Adicione `VITE_API_URL` com a URL do seu backend (ex: `https://seu-backend.com` ou `https://seu-servidor.railway.app`)
   - Vercel vai fazer build automaticamente com essa env

4. **Deploy via Git:**
   ```bash
   git push origin main  # Vercel puxa automaticamente
   ```
   Ou manualmente: `npx vercel --prod`

**Importante:** O backend (FastAPI) precisa estar hospedado em outro lugar (Railway, Fly.io, seu servidor, etc.) com CORS configurado. O frontend precisa acessá-lo via URL pública — não pode ser `http://localhost:8000`.

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
O backend usa os modelos configurados em `LLM_PRIMARY_MODEL`/`LLM_FALLBACK_MODEL`
(veja `.env.example` na raiz do projeto) e rejeita respostas que parecem
racionínio vazado em inglês, tentando o modelo de fallback automaticamente
(veja `_reject_leaked_reasoning` em `frontend_api.py`).

## Níveis das cartas
A API devolve nível relativo à raridade. O front normaliza usando o maior `maxLevel`
da coleção (o das comuns), então não há número mágico para atualizar quando o jogo subir o teto.
