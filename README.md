# talentos-site

TalentOS brand website (Astro, static, zero client JS). ## Deploy (current)
Pages serves the `gh-pages` branch (build_type=legacy). Run `./deploy.sh` (build + force-push dist/ to gh-pages).
The gh token on the box lacks the `workflow` scope, so the Actions workflow (withastro/action) is parked at `deploy/deploy.yml`.
To switch to Actions: `gh auth refresh -s workflow` (Jimmy signs in), `mkdir -p .github/workflows && git mv deploy/deploy.yml .github/workflows/`, push, then
`gh api -X PUT repos/JimmyWangJimmy/talentos-site/pages -f build_type=workflow`.

## Edit content
Page copy: `src/content/pages/*.md` (same format as the copy deck: `# 中文` then `# English`, one `## ` per block; first block = hero, bold first line = h1; 次要入口/Secondary entry blocks render as a slim bar; `meta.md` table = titles/descriptions). Nav/footer strings:
- `zh.json` — Chinese (served at `/`)
- `en.json` — English (served at `/en/`)
- `theme.json` — colors
Logo: replace `public/logo.svg` and `public/favicon.svg`.
Keep the JSON keys; only change values. Run `npm run build` to check, then push to `main`.

## Switch to www.agentbay.asia (after the DNS CNAME www -> jimmywangjimmy.github.io exists)
1. In `astro.config.mjs` change the defaults to `site: 'https://www.agentbay.asia'`, `base: '/'` (or set SITE_URL/SITE_BASE env in deploy.sh / the workflow).
2. `cp CNAME.custom-domain public/CNAME`
3. Commit + push to main, then `./deploy.sh`.
4. IT运维 sets the Pages custom domain: `gh api -X PUT repos/JimmyWangJimmy/talentos-site/pages -f cname=www.agentbay.asia`
5. When the certificate is issued (check `gh api repos/JimmyWangJimmy/talentos-site/pages --jq .https_certificate.state` = `approved`):
   `gh api -X PUT repos/JimmyWangJimmy/talentos-site/pages -F https_enforced=true`
Do not touch the root domain or MX/SPF/DKIM records.
