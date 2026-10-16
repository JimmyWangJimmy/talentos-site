# Preview: phone callback form

**Branch:** `preview/callback-form`  
**Do not** merge to `main` or run `./deploy.sh` (production gh-pages) until boss accepts preview.

## Local preview

```bash
cd /workspace/site/talentos-site
# Point form at local Worker or workers.dev:
PUBLIC_CALLBACK_API_BASE=http://127.0.0.1:8787 npm run dev
# open http://localhost:4321/contact/#callback
# EN: http://localhost:4321/en/contact/#callback
```

Worker (mock without key):

```bash
cd /workspace/site/callback-api
npm install && npx wrangler dev
```

## After Worker deploy

```bash
PUBLIC_CALLBACK_API_BASE=https://talentos-callback-api.<account>.workers.dev npm run build
# Inspect dist/ only — do not force-push gh-pages for production cutover
```

Production form base: `https://api.agentbay.asia` (default in `src/config/callback.js`).
