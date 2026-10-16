# Preview: phone callback form

**Branch:** `preview/callback-form`  
**Do not** merge to `main` or run `./deploy.sh` (production gh-pages) until boss accepts preview.

## API (preview)

- Worker: `https://talentos-callback-api.jimmywangjimmy.workers.dev`
- Boss chose **A**: long-term workers.dev; `api.agentbay.asia` CNAME optional placeholder (no TLS). Brand domain later = option C.
- Mode: **mock** until `wrangler secret put SPEKO_API_KEY` (no live dial)

## Local site preview

```bash
cd /workspace/site/talentos-site
PUBLIC_CALLBACK_API_BASE=https://talentos-callback-api.jimmywangjimmy.workers.dev npm run dev
# ZH: http://localhost:4321/contact/#callback
# EN: http://localhost:4321/en/contact/#callback
```

## Worker

```bash
cd /workspace/site/callback-api
npm install
npx wrangler deploy          # already deployed once
npx wrangler secret put SPEKO_API_KEY   # production key only — not 测试工程师 key
```

Before first live dial: send number + firstMessage + duration to 测试工程师; boss confirms number.
