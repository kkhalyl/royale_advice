# 🚀 Deployment Guide

Royal Advice has **two separate deployments**: frontend on Vercel, backend on Railway/Render/Fly.io.

---

## Part 1: Push to GitHub

Before deploying anywhere, your code needs to be on GitHub.

### 1.1 Create GitHub Repo

Go to https://github.com/new and create `royal-advice` (private recommended).

### 1.2 Push Local Code

```bash
# From project root
git remote add origin https://github.com/YOUR_USERNAME/royal-advice.git
git branch -M main
git push -u origin main
```

✅ Code is now on GitHub.

---

## Part 2: Deploy Frontend to Vercel

### 2.1 Connect GitHub to Vercel

1. Go to https://vercel.com/dashboard
2. Click **"Add New..." → "Project"**
3. Import `royal-advice` repo
4. Vercel auto-detects Vite (frontend framework)
5. Set root directory: `frontend/`

### 2.2 Set Environment Variables

In Vercel Dashboard → Settings → Environment Variables:
```
VITE_API_URL=https://your-backend-url.com
```

Examples of backend URLs:
- Railway: `https://royal-advice-prod.up.railway.app`
- Render: `https://royal-advice.onrender.com`
- Fly.io: `https://royal-advice.fly.dev`

### 2.3 Deploy

```bash
git push origin main
```

Vercel auto-deploys on every push. Done! ✅

Frontend lives at: `https://your-project.vercel.app`

---

## Part 3: Deploy Backend to Railway

### 3.1 Connect GitHub to Railway

1. Go to https://railway.app
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Authorize GitHub and select `royal-advice`

### 3.2 Configure Build & Start Commands

Railway should auto-detect Python. If not, set:

**Build Command:**
```
pip install -r requirements.txt
```

**Start Command:**
```
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3.3 Set Environment Variables

In Railway → Variables:
```
GEMINI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
ROYALE_API_KEY=your_key_here
LLM_PRIMARY_MODEL=gemini-3.1-flash-lite
GROQ_FALLBACK_MODEL=gsk_...
REDDIT_CLIENT_ID=your_id_here
REDDIT_CLIENT_SECRET=your_secret_here
```

### 3.4 Deploy

Railway auto-deploys on every push. Done! ✅

Backend URL: `https://royal-advice-prod.up.railway.app` (shown in Railway dashboard)

---

## Part 4: Connect Frontend ↔ Backend

Once backend is live, update Vercel's `VITE_API_URL`:

1. Vercel Dashboard → Settings → Environment Variables
2. Set `VITE_API_URL=https://your-railway-backend-url`
3. Trigger redeploy: `git push origin main` or click "Redeploy" in Vercel

---

## Part 5: Test Everything

1. Go to your frontend URL: `https://your-project.vercel.app`
2. Look up a Clash Royale player (e.g., tag: `2PP`)
3. Click "Ask the Witch" and ask a question
4. Should get a response from your live backend ✅

---

## Troubleshooting

### "API not found" or 404 errors from frontend
- Check Vercel's `VITE_API_URL` is correct
- Backend needs CORS enabled (should be by default in `app/main.py`)
- Trigger Vercel redeploy after updating `VITE_API_URL`

### Backend responds slowly on first request
- **Free tier Render/Railway sleep after inactivity** — upgrade to paid, or use Railway's credits
- First wake-up takes 10-30s; subsequent requests are fast

### "500 Backend Error" or LLM failures
- Check Railway/Render logs for error details
- Verify all `.env` variables are set in the hosting dashboard (not locally)
- Ensure API keys are valid and haven't expired

### "ROYALE_API_KEY: 403 Forbidden"
- Check RoyaleAPI dashboard: add `45.79.218.79` to **ALLOWED IP ADDRESSES**
- May take a few minutes to propagate

---

## Local Development Reminders

After deploying, you can still run locally with `.bat` scripts:

```bash
run-backend.bat   # Backend at localhost:8000
```

```bash
cd frontend && run-frontend.bat  # Frontend at localhost:5173
```

Frontend will use `VITE_API_URL=http://localhost:8000` from `frontend/.env`.

---

## Cost Estimate (Monthly)

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| **Vercel (frontend)** | Unlimited static | N/A (included) |
| **Railway (backend)** | $5 credits/month | $5-15/month typical |
| **Render (backend, alt)** | 1 service sleeps | $7/month (always on) |
| **Fly.io (backend, alt)** | 3x 256MB shared | $5+/month |

**Recommendation:** Start with Railway's free credits (~$5/month). As usage grows, upgrade to paid ($5-15/month) or switch to Fly.io ($5+/month).

---

## Auto-Deployment After Git Push

All three platforms (Vercel, Railway, Render, Fly.io) auto-deploy when you push to `main`:

```bash
git add .
git commit -m "Update feature X"
git push origin main
# → Automatic deployment in ~30-60 seconds
```

No manual steps needed after the initial setup! 🎉
