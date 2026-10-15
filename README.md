# talentos-site

TalentOS brand website (Astro, static, zero client JS). Deployed to GitHub Pages by `.github/workflows/deploy.yml`.

## Edit content
All copy lives in `src/content/`:
- `zh.json` — Chinese (served at `/`)
- `en.json` — English (served at `/en/`)
- `theme.json` — colors (accent / ink / muted / bg / line)
Logo: replace `public/logo.svg` and `public/favicon.svg`.
Keep the JSON keys; only change values. Run `npm run build` to check, then push to `main`.

## Switch to www.agentbay.asia (after the DNS CNAME www -> jimmywangjimmy.github.io exists)
1. In `.github/workflows/deploy.yml` set `SITE_URL: https://www.agentbay.asia` and `SITE_BASE: /`.
2. `cp CNAME.custom-domain public/CNAME`
3. Commit + push to main.
4. `gh api -X PUT repos/JimmyWangJimmy/talentos-site/pages -f cname=www.agentbay.asia`
5. When the certificate is issued (check `gh api repos/JimmyWangJimmy/talentos-site/pages --jq .https_certificate.state` = `approved`):
   `gh api -X PUT repos/JimmyWangJimmy/talentos-site/pages -F https_enforced=true`
Do not touch the root domain or MX/SPF/DKIM records.
